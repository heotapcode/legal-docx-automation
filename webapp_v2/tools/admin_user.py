"""Quản lý tài khoản quản trị từ dòng lệnh (chạy trong thư mục webapp_v2).

    python -m tools.admin_user create <tên>     tạo tài khoản (hỏi mật khẩu, không hiện khi gõ)
    python -m tools.admin_user passwd <tên>     đổi mật khẩu (đăng xuất mọi phiên của tài khoản)
    python -m tools.admin_user disable <tên>    khóa tài khoản
    python -m tools.admin_user enable <tên>     mở khóa tài khoản
    python -m tools.admin_user list             danh sách tài khoản

Mật khẩu không bao giờ nhận qua tham số dòng lệnh (tránh lưu vào lịch sử shell).
"""
import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import auth  # noqa: E402


def _ask_password() -> str:
    pw = getpass.getpass("Mật khẩu: ")
    if pw != getpass.getpass("Nhập lại mật khẩu: "):
        raise ValueError("Hai lần nhập mật khẩu không khớp")
    return pw


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.admin_user", description="Quản lý tài khoản quản trị")
    ap.add_argument("command", choices=["create", "passwd", "disable", "enable", "list"])
    ap.add_argument("username", nargs="?")
    args = ap.parse_args(argv)
    try:
        if args.command == "list":
            for u in auth.list_users():
                state = "hoạt động" if u["is_active"] else "đã khóa"
                print(f"{u['username']}\t{u['role']}\t{state}\t{u['created_at']}")
            return 0
        if not args.username:
            ap.error("cần <tên> đăng nhập")
        if args.command == "create":
            auth.create_user(args.username, _ask_password())
            print(f"Đã tạo tài khoản {args.username}")
        elif args.command == "passwd":
            auth.set_password(args.username, _ask_password())
            print(f"Đã đổi mật khẩu {args.username}")
        else:
            auth.set_active(args.username, args.command == "enable")
            print(f"Đã {'mở khóa' if args.command == 'enable' else 'khóa'} {args.username}")
    except ValueError as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
