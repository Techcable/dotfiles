# TouchId for Sudo

To make touchid authorization work for sudo, add the following line to `/etc/pam.d/sudo`:

```
auth       sufficient     pam_tid.so
```

Source: https://www.imore.com/how-use-sudo-your-mac-touch-id

**WARNING**: This is dangerous

