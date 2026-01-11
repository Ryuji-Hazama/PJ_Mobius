# Project Mobius

## Requirements

### Files

You need to add following files into `Server/secrets`:

- `mysql_password.txt`: MySQL user password
- `mysql_user.txt`: MySQL user name
- `root_password.txt`: MySQL root password
- `server_admin_name`: Server application administrator name
- `server_admin_password`: Server application administrator hashed password

### Packages

#### PIP Packages

You need to run the following command to install requirements in both `Server` and `Client`

```bash
pip install -r requirements.txt
```

#### tkinter

You need to run the following command to install `tkinter` and `PIL.ImageTk` to ensure using `ttkbootstrap` (`tkinter` based).

```bash
sudo apt install scrot python3-tk python3-dev python3-pil.imagetk
```
