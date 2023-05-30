# Automatically Make TX DMV Appointments

Because who has time to wait

## Usage

## reCAPTCHA

You are not technically supposed to do this. But sshhhhh....

I found that after I left this running for a while, I started being blocked by reCAPTCHA failures. One way to get around that is to use a VPN so that your requests are coming from a different server.

Here's an easy command to abuse your SSH access to some other server:

```shell
sshuttle --dns -vr hostname@server 0/0 --ssh-cmd 'ssh'
```
