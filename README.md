# Automatically Make TX DMV Appointments

Because who has time to wait

## Installation

You need [poetry](https://python-poetry.org/docs/) installed.

Then `poetry install` will install dependencies for you. Then, fill in your information in`sample.toml`.

To run:

```shell
poetry run python auto-tx-dmv/auto-dmv.py sample.toml
```

## Usage

## reCAPTCHA

You are not technically supposed to do this. But sshhhhh....

I found that after I left this running for a while, I started being blocked by reCAPTCHA failures. One way to get around that is to use a VPN so that your requests are coming from a different server.

Here's an easy command to abuse your SSH access to some other server:

```shell
sshuttle --dns -vr hostname@server 0/0 --ssh-cmd 'ssh'
```
