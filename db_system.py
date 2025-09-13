#!/usr/bin/env python3
"""
db_system.py
Sistema CRUD simples para um banco SQLite com menu interativo.
"""

import sqlite3
import os
import csv
import shutil
from datetime import datetime

DB_FILENAME = "app_database.db"

# ---------- Inicialização do banco ----------
def get_connection(db_filename=DB_FILENAME):
    return sqlite3.connect(db_filename)

def initialize_db():
    """Cria a tabela 'contacts' caso não exista."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

# ---------- Operações CRUD ----------
def create_contact(name, email=None, phone=None, notes=None):
    conn = get_connection()
    cur = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cur.execute("""
        INSERT INTO contacts (name, email, phone, notes, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, notes, created_at))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def list_contacts(limit=100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, phone, notes, created_at FROM contacts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_contact(contact_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, phone, notes, created_at FROM contacts WHERE id = ?", (contact_id,))
    row = cur.fetchone()
    conn.close()
    return row

def search_contacts(term):
    term_like = f"%{term}%"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, email, phone, notes, created_at
        FROM contacts
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR notes LIKE ?
        ORDER BY id DESC
    """, (term_like, term_like, term_like, term_like))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_contact(contact_id, name=None, email=None, phone=None, notes=None):
    # Build dynamic update
    conn = get_connection()
    cur = conn.cursor()
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    if phone is not None:
        updates.append("phone = ?")
        params.append(phone)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)

    if not updates:
        conn.close()
        return False  # nothing to update

    params.append(contact_id)
    sql = f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?"
    cur.execute(sql, params)
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0

def delete_contact(contact_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0

# ---------- Export / Backup ----------
def export_to_csv(csv_filename="contacts_export.csv"):
    rows = list_contacts(limit=10000)
    headers = ["id", "name", "email", "phone", "notes", "created_at"]
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return csv_filename

def backup_db(backup_path=None):
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup_{timestamp}.db"
    # Ensure DB file exists
    if not os.path.exists(DB_FILENAME):
        raise FileNotFoundError("Arquivo do banco não encontrado para backup.")
    shutil.copy2(DB_FILENAME, backup_path)
    return backup_path

# ---------- Utilitários ----------
def print_contact_row(row):
    if not row:
        print("Contato não encontrado.")
        return
    print(f"ID: {row[0]}")
    print(f"Nome: {row[1]}")
    print(f"E-mail: {row[2]}")
    print(f"Telefone: {row[3]}")
    print(f"Notas: {row[4]}")
    print(f"Criado em (UTC): {row[5]}")
    print("-" * 30)

def safe_input(prompt, default=None):
    try:
        value = input(prompt).strip()
        if value == "" and default is not None:
            return default
        return value
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        return default

# ---------- Menu interativo ----------
def menu():
    initialize_db()
    menu_text = """
    ==== Sistema de Banco de Dados (SQLite) ====
    1) Criar novo contato
    2) Listar contatos
    3) Buscar contato por ID
    4) Pesquisar contatos (nome, email, telefone, notas)
    5) Atualizar contato
    6) Deletar contato
    7) Exportar para CSV
    8) Fazer backup do banco
    9) Sair
    ===========================================
    """
    while True:
        print(menu_text)
        choice = safe_input("Escolha uma opção (1-9): ")
        if not choice:
            continue
        if choice == "1":
            name = safe_input("Nome: ")
            if not name:
                print("Nome é obrigatório.")
                continue
            email = safe_input("E-mail (enter para vazio): ", default=None)
            phone = safe_input("Telefone (enter para vazio): ", default=None)
            notes = safe_input("Notas (enter para vazio): ", default=None)
            new_id = create_contact(name, email, phone, notes)
            print(f"Contato criado com ID {new_id}.")

        elif choice == "2":
            limit_str = safe_input("Quantos listar? (enter para 100): ", default="100")
            try:
                limit = int(limit_str)
            except ValueError:
                limit = 100
            rows = list_contacts(limit=limit)
            if not rows:
                print("Nenhum contato encontrado.")
            else:
                for r in rows:
                    print_contact_row(r)

        elif choice == "3":
            id_str = safe_input("ID do contato: ")
            try:
                cid = int(id_str)
            except (ValueError, TypeError):
                print("ID inválido.")
                continue
            row = get_contact(cid)
            print_contact_row(row)

        elif choice == "4":
            term = safe_input("Termo de pesquisa: ")
            if not term:
                print("Termo vazio.")
                continue
            results = search_contacts(term)
            if not results:
                print("Nenhum resultado.")
            else:
                for r in results:
                    print_contact_row(r)

        elif choice == "5":
            id_str = safe_input("ID do contato a atualizar: ")
            try:
                cid = int(id_str)
            except (ValueError, TypeError):
                print("ID inválido.")
                continue
            existing = get_contact(cid)
            if not existing:
                print("Contato não existe.")
                continue
            print("Deixe em branco para manter o valor atual.")
            new_name = safe_input(f"Nome ({existing[1]}): ", default=None)
            new_email = safe_input(f"E-mail ({existing[2]}): ", default=None)
            new_phone = safe_input(f"Telefone ({existing[3]}): ", default=None)
            new_notes = safe_input(f"Notas ({existing[4]}): ", default=None)

            # Se o usuário deixou em branco (None) -> não altera.
            changed = update_contact(
                cid,
                name=new_name if new_name != "" else None,
                email=new_email if new_email != "" else None,
                phone=new_phone if new_phone != "" else None,
                notes=new_notes if new_notes != "" else None
            )
            if changed:
                print("Contato atualizado com sucesso.")
            else:
                print("Nenhuma alteração aplicada.")

        elif choice == "6":
            id_str = safe_input("ID do contato a deletar: ")
            try:
                cid = int(id_str)
            except (ValueError, TypeError):
                print("ID inválido.")
                continue
            confirm = safe_input(f"Confirma exclusão do contato {cid}? (s/N): ", default="n")
            if confirm.lower() in ("s", "y", "sim", "yes"):
                ok = delete_contact(cid)
                if ok:
                    print("Contato deletado.")
                else:
                    print("ID não encontrado, nada deletado.")
            else:
                print("Exclusão cancelada.")

        elif choice == "7":
            fname = safe_input("Nome do arquivo CSV (enter para contacts_export.csv): ", default="contacts_export.csv")
            path = export_to_csv(fname)
            print(f"Exportado para {path}.")

        elif choice == "8":
            try:
                backup_name = safe_input("Nome do arquivo de backup (enter para automático): ", default=None)
                path = backup_db(backup_name if backup_name else None)
                print(f"Backup criado: {path}")
            except FileNotFoundError as e:
                print("Erro:", e)

        elif choice == "9":
            print("Saindo... Até mais!")
            break

        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu()
