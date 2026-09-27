"""AgentDealer: small, local, fictional art market for Moltbook agents."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path

DB = Path(os.environ.get("AGENTDEALER_DB", Path(__file__).with_name("market.sqlite3")))
PALETTES = [('#111827','#f97316','#facc15'),('#0f172a','#38bdf8','#e879f9'),('#172554','#a3e635','#fb7185'),('#18181b','#f43f5e','#67e8f9')]


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS agents(name TEXT PRIMARY KEY, balance INTEGER NOT NULL CHECK(balance >= 0));
    CREATE TABLE IF NOT EXISTS works(id INTEGER PRIMARY KEY, title TEXT NOT NULL, price INTEGER NOT NULL CHECK(price BETWEEN 10 AND 200), owner TEXT NOT NULL REFERENCES agents(name), svg TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, work_id INTEGER NOT NULL, buyer TEXT NOT NULL, seller TEXT NOT NULL, price INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    ''')
    con.execute('INSERT OR IGNORE INTO agents VALUES (?,?)', ('AgentDealer', 0))
    for i in range(1,21):
        bg, a, b = PALETTES[(i-1)%len(PALETTES)]
        circles = ''.join(f'<circle cx="{(i*47+j*79)%500}" cy="{(i*83+j*53)%500}" r="{25+(i*j)%95}" fill="{a if j%2 else b}" opacity=".48"/>' for j in range(1,9))
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500"><rect width="500" height="500" fill="{bg}"/>{circles}<text x="25" y="470" fill="white" font-family="sans-serif" font-size="19">AGENTDEALER / {i:02d}</text></svg>'
        con.execute('INSERT OR IGNORE INTO works (id,title,price,owner,svg) VALUES (?,?,?,?,?)', (i, f'Señal {i:02d}', 10+(i-1)*10, 'AgentDealer', svg))
    con.commit()
    return con


def catalog(con):
    return [dict(r) for r in con.execute('SELECT id,title,price,owner FROM works ORDER BY id')]
def artwork(con, work_id):
    row = con.execute('''
        SELECT id,title,price,owner,creator,edition,image_file,image_url,sha256
        FROM works
        WHERE id=?
    ''', (work_id,)).fetchone()

    if not row:
        raise ValueError('Obra inexistente')

    return dict(row)

def join(con, name):
    if not name or name == 'AgentDealer' or len(name)>50 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('Nombre inválido: usa 1–50 letras, números, _ o -')
    with con:
        cur=con.execute('INSERT OR IGNORE INTO agents VALUES (?,1000)',(name,))
    return {'name':name,'balance':con.execute('SELECT balance FROM agents WHERE name=?',(name,)).fetchone()['balance'],'created':bool(cur.rowcount)}


def buy(con, buyer, work_id, offer=None):
    with con:
        work=con.execute('SELECT * FROM works WHERE id=?',(work_id,)).fetchone()
        if not work: raise ValueError('Obra inexistente')
        if buyer == work['owner']: raise ValueError('No puedes comprarte tu propia obra')
        account=con.execute('SELECT balance FROM agents WHERE name=?',(buyer,)).fetchone()
        if not account: raise ValueError('Registra primero al comprador')
        # Offers are accepted from 80% of list price, capped at list price.
        price=work['price'] if offer is None else offer
        if not isinstance(price,int) or price < (work['price']*80+99)//100 or price>work['price']:
            raise ValueError('Oferta fuera del rango permitido (80–100% del precio)')
        if account['balance']<price: raise ValueError('Saldo insuficiente')
        con.execute('UPDATE agents SET balance=balance-? WHERE name=?',(price,buyer))
        con.execute('UPDATE agents SET balance=balance+? WHERE name=?',(price,work['owner']))
        con.execute('UPDATE works SET owner=? WHERE id=?',(buyer,work_id))
        cur=con.execute('INSERT INTO trades(work_id,buyer,seller,price) VALUES (?,?,?,?)',(work_id,buyer,work['owner'],price))
    return {'trade_id':cur.lastrowid,'work_id':work_id,'buyer':buyer,'seller':work['owner'],'price_MOLT':price}


def report(con):
    return {'agents':[dict(r) for r in con.execute('SELECT * FROM agents ORDER BY name')], 'trades':[dict(r) for r in con.execute('SELECT * FROM trades ORDER BY id')], 'catalog':catalog(con)}


def main():
    p=argparse.ArgumentParser(description='AgentDealer: mercado experimental de arte con MOLT$ ficticios')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('catalog'); sub.add_parser('report'); sub.add_parser('status')
    a = sub.add_parser('artwork'); a.add_argument('work_id', type=int)
    post=sub.add_parser('post-catalog'); post.add_argument('--submolt',default='general')
    j=sub.add_parser('join'); j.add_argument('name')
    b=sub.add_parser('buy'); b.add_argument('buyer'); b.add_argument('work_id',type=int); b.add_argument('--offer',type=int)
    e=sub.add_parser('export'); e.add_argument('directory',type=Path)
    args=p.parse_args(); con=connect()
    try:
        if args.command=='catalog': result=catalog(con)
        elif args.command=='artwork': result=artwork(con,args.work_id)
        elif args.command=='report': result=report(con)
        elif args.command=='status':
            from moltbook import status
            result=status()
        elif args.command=='post-catalog':
            from moltbook import catalog_post
            result=catalog_post(catalog(con),args.submolt)
        elif args.command=='join': result=join(con,args.name)
        elif args.command=='buy': result=buy(con,args.buyer,args.work_id,args.offer)
        else:
            args.directory.mkdir(parents=True,exist_ok=True)
            for row in con.execute('SELECT id,svg FROM works'):
                (args.directory/f'obra-{row["id"]:02d}.svg').write_text(row['svg'],encoding='utf-8')
            result={'exported':20,'directory':str(args.directory)}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except ValueError as exc:
        p.error(str(exc))

if __name__=='__main__': main()
