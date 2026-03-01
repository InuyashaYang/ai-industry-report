#!/usr/bin/env python3
"""
send_report.py — 飞书文档导出 PDF + QQ 邮件发送

用法:
  python3 send_report.py --token <doc_token> --title "国智投洞见第N期" --to xxx@qq.com

依赖环境变量（已在 openclaw.json 中配置）:
  SMTP_USER  SMTP_PASS  SMTP_HOST  SMTP_PORT
  FEISHU_APP_ID  FEISHU_APP_SECRET
"""

import os, sys, json, time, smtplib, ssl, tempfile, argparse, subprocess
from pathlib import Path
from email.message import EmailMessage

# ── Feishu 配置 ───────────────────────────────────────────────────
APP_ID     = os.environ.get('FEISHU_APP_ID', '')
APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
FEISHU_API = 'https://open.feishu.cn/open-apis'

# ── SMTP 配置 ─────────────────────────────────────────────────────
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))


def feishu_request(method: str, path: str, token: str, **kwargs) -> dict:
    """通用飞书 API 请求（用 curl 走代理）"""
    url = f'{FEISHU_API}{path}'
    headers = [
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
    ]
    data_args = []
    if 'json' in kwargs:
        data_args = ['-d', json.dumps(kwargs['json'], ensure_ascii=False)]
    if 'params' in kwargs:
        qs = '&'.join(f'{k}={v}' for k, v in kwargs['params'].items())
        url = f'{url}?{qs}'

    cmd = ['curl', '-sf', '--max-time', '30', '-X', method.upper(),
           url, *headers, *data_args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
    if r.returncode != 0:
        raise RuntimeError(f'curl error: {r.stderr[:200]}')
    return json.loads(r.stdout)


def get_tenant_token() -> str:
    """获取飞书 tenant_access_token"""
    r = subprocess.run(
        ['curl', '-sf', '--max-time', '15',
         f'{FEISHU_API}/auth/v3/tenant_access_token/internal',
         '-H', 'Content-Type: application/json',
         '-d', json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET})],
        capture_output=True, text=True, timeout=20
    )
    d = json.loads(r.stdout)
    token = d.get('tenant_access_token', '')
    if not token:
        raise RuntimeError(f'获取 token 失败: {d}')
    return token


def export_to_pdf(doc_token: str, tenant_token: str, out_dir: str = '/tmp') -> str:
    """
    飞书文档 → PDF，返回本地文件路径
    """
    print(f'[1/3] 创建导出任务 (doc_token={doc_token})...', flush=True)
    resp = feishu_request('POST', '/drive/v1/export_tasks', tenant_token, json={
        'file_extension': 'pdf',
        'token': doc_token,
        'type': 'docx',
    })
    code = resp.get('code', -1)
    if code != 0:
        raise RuntimeError(f'创建导出任务失败: {resp}')

    ticket = resp['data']['ticket']
    print(f'[2/3] 轮询导出状态 (ticket={ticket})...', flush=True)

    file_token = None
    for _ in range(20):
        time.sleep(3)
        poll = feishu_request('GET', f'/drive/v1/export_tasks/{ticket}',
                              tenant_token, params={'token': doc_token})
        job = poll.get('data', {}).get('result', {})
        status = job.get('job_status', -1)
        if status == 0:
            file_token = job['file_token']
            file_name  = job.get('file_name', f'{doc_token}.pdf')
            if not file_name.endswith('.pdf'):
                file_name += '.pdf'
            break
        elif status in (3, 4):
            raise RuntimeError(f'导出失败: {job}')
        # status 1/2 = 处理中，继续等

    if not file_token:
        raise RuntimeError('导出超时')

    print(f'[3/3] 下载 PDF (file_token={file_token})...', flush=True)
    out_path = str(Path(out_dir) / file_name)
    dl_cmd = [
        'curl', '-sf', '--max-time', '60',
        f'{FEISHU_API}/drive/v1/medias/{file_token}/download',
        '-H', f'Authorization: Bearer {tenant_token}',
        '-L', '-o', out_path,
    ]
    r = subprocess.run(dl_cmd, capture_output=True, timeout=65)
    if r.returncode != 0:
        raise RuntimeError(f'下载失败: {r.stderr[:100]}')

    size = Path(out_path).stat().st_size
    print(f'✅ PDF 下载完成 → {out_path} ({size//1024} KB)', flush=True)
    return out_path


def send_email(to: str, subject: str, body: str, attachment_path: str = None):
    """QQ SMTP 发送邮件（可附件）"""
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError('SMTP_USER / SMTP_PASS 未配置')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From']    = SMTP_USER
    msg['To']      = to
    msg.set_content(body)

    if attachment_path and Path(attachment_path).exists():
        with open(attachment_path, 'rb') as f:
            data = f.read()
        fname = Path(attachment_path).name
        msg.add_attachment(data, maintype='application', subtype='pdf',
                           filename=fname)
        print(f'📎 附件: {fname} ({len(data)//1024} KB)', flush=True)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

    print(f'✅ 邮件已发送 → {to}', flush=True)


def run(doc_token: str, title: str, to: str, body: str = None):
    """主流程：导出 PDF → 发邮件"""
    # 自动从 openclaw.json 补充 Feishu 凭证（如未通过环境变量传入）
    global APP_ID, APP_SECRET
    if not APP_ID or not APP_SECRET:
        try:
            cfg = json.load(open('/home/inuyasha/.openclaw/openclaw.json'))
            feishu_ch = cfg.get('channels', {}).get('feishu', {})
            acct = feishu_ch.get('accounts', {}).get('default', {})
            APP_ID     = acct.get('appId', '')
            APP_SECRET = acct.get('appSecret', '')
        except Exception as e:
            raise RuntimeError(f'无法读取飞书凭证: {e}')

    tenant_token = get_tenant_token()
    pdf_path = export_to_pdf(doc_token, tenant_token)

    email_body = body or (
        f'您好，\n\n《{title}》已生成，请见附件 PDF。\n\n'
        f'— 国智投 · OpenClaw AI 研究助手'
    )
    send_email(to=to, subject=title, body=email_body, attachment_path=pdf_path)

    # 清理临时文件
    try:
        Path(pdf_path).unlink()
    except Exception:
        pass

    return pdf_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='飞书文档导出 PDF 并发送邮件')
    ap.add_argument('--token', required=True, help='飞书文档 token')
    ap.add_argument('--title', required=True, help='邮件主题 / 文档标题')
    ap.add_argument('--to',    required=True, help='收件人邮箱')
    ap.add_argument('--body',  default=None,  help='邮件正文（可选）')
    args = ap.parse_args()

    run(doc_token=args.token, title=args.title, to=args.to, body=args.body)
