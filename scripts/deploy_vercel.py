"""Invoke an owner's Vercel deploy hook without printing its secret URL."""
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

hook=os.getenv('VERCEL_DEPLOY_HOOK','')
parts=urlsplit(hook)
if parts.scheme!='https' or parts.netloc!='api.vercel.com' or not parts.path.startswith('/v1/integrations/deploy/'):
    raise SystemExit('Set the VERCEL_DEPLOY_HOOK Actions secret to your Vercel deploy hook URL.')
try:
    with urlopen(Request(hook,data=b'',method='POST'),timeout=30) as response:
        if response.status not in (200,201,202):raise ValueError()
    print('Vercel deployment requested. Check Vercel Deployments for build completion.')
except Exception:
    raise SystemExit('Vercel deploy hook failed. Check hook configuration and network access.') from None
