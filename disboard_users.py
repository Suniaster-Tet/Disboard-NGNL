#!/usr/bin/env python3
"""Manage the local allowlist; access keys are displayed only when created."""
import argparse
from disboard_access import AccessRegistry


def main():
    parser = argparse.ArgumentParser(description="Administrar accesos locales de Disboard.")
    commands = parser.add_subparsers(dest="command", required=True)
    add_command = commands.add_parser("add", help="Registrar un usuario y generar su llave")
    add_command.add_argument("username")
    commands.add_parser("list", help="Listar usuarios autorizados")
    revoke_command = commands.add_parser("revoke", help="Revocar usuario y sus sesiones")
    revoke_command.add_argument("username")
    args = parser.parse_args()
    registry = AccessRegistry()

    if args.command == "add":
        try:
            access_key = registry.add_user(args.username)
        except Exception as error:
            parser.error(str(error))
        print(f"Usuario: {args.username}")
        print("Llave de acceso (se muestra una sola vez; entrégala por un canal seguro):")
        print(access_key)
    elif args.command == "list":
        for user in registry.list_users():
            state = "activo" if user["active"] else "revocado"
            print(f"{user['username']} ({state})")
    elif args.command == "revoke":
        if not registry.revoke_user(args.username):
            parser.error("No existe ese usuario.")
        print(f"Acceso revocado: {args.username}")


if __name__ == "__main__":
    main()