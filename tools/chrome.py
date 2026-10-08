"""Find a headless Chrome: $CHROME_PATH, else the newest chrome-headless-shell that Puppeteer installed."""
import glob
import os


def chrome_path():
    if os.environ.get('CHROME_PATH'):
        return os.environ['CHROME_PATH']
    found = sorted(glob.glob(os.path.expanduser('~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell')))
    if not found:
        raise SystemExit('No headless Chrome: run `npx @puppeteer/browsers install chrome-headless-shell@stable`, or set CHROME_PATH')
    return found[-1]
