from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import connect_db

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'

# ========== LOGIN & REGISTRO ==========

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = connect_db()
    cursor = db.cursor()
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        cursor.execute("SELECT id, senha FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user[1], senha):
            session['user_id'] = user[0]
            return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = connect_db()
    cursor = db.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, senha))
        db.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ========== DASHBOARD E SIMULAÇÕES ==========


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    rodada_id = request.args.get('rodada', type=int)
    
    db = connect_db()
    cursor = db.cursor()
    
    if rodada_id:
        cursor.execute("""
            SELECT j.id, j.rodada, t1.nome AS time_casa, t2.nome AS time_fora 
            FROM jogos j
            JOIN times t1 ON j.time_casa_id = t1.id
            JOIN times t2 ON j.time_fora_id = t2.id
            WHERE j.rodada = %s
            ORDER BY j.rodada, j.ordem
        """, (rodada_id,))
    else:
        cursor.execute("""
            SELECT j.id, j.rodada, t1.nome AS time_casa, t2.nome AS time_fora 
            FROM jogos j
            JOIN times t1 ON j.time_casa_id = t1.id
            JOIN times t2 ON j.time_fora_id = t2.id
            ORDER BY j.rodada, j.ordem
        """)
    
    jogos = cursor.fetchall()
    
    # Para obter as rodadas disponíveis
    cursor.execute("SELECT DISTINCT rodada FROM jogos ORDER BY rodada")
    rodadas = cursor.fetchall()

    return render_template('dashboard.html', jogos=jogos, rodadas=rodadas)



@app.route('/simular/<int:jogo_id>', methods=['GET', 'POST'])
def simular(jogo_id):
    if 'user_id' not in session:
        return redirect('/login')
    db = connect_db()
    cursor = db.cursor()

    if request.method == 'POST':
        gols_casa = int(request.form['gols_casa'])
        gols_fora = int(request.form['gols_fora'])
        shootout = 'shootout' in request.form
        vencedor = request.form.get('vencedor_shootout') if shootout else None

        cursor.execute("""
            INSERT INTO simulacoes (usuario_id, jogo_id, gols_casa, gols_fora, teve_shootout, vencedor_shootout)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            gols_casa=VALUES(gols_casa),
            gols_fora=VALUES(gols_fora),
            teve_shootout=VALUES(teve_shootout),
            vencedor_shootout=VALUES(vencedor_shootout)
        """, (session['user_id'], jogo_id, gols_casa, gols_fora, shootout, vencedor))
        db.commit()
        return redirect('/dashboard')

    # dados do jogo
    cursor.execute("""
        SELECT t1.nome, t2.nome FROM jogos
        JOIN times t1 ON jogos.time_casa_id = t1.id
        JOIN times t2 ON jogos.time_fora_id = t2.id
        WHERE jogos.id = %s
    """, (jogo_id,))
    jogo = cursor.fetchone()
    return render_template('simulacao.html', jogo=jogo, jogo_id=jogo_id)

# ========== TABELA CLASSIFICATIVA ==========

@app.route('/tabela')
def tabela():
    if 'user_id' not in session:
        return redirect('/login')
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome FROM times")
    times = {tid: {'nome': nome, 'pts': 0, 'j': 0, 'v': 0, 'e': 0, 'd': 0, 'gp': 0, 'gc': 0, 'sg': 0} for tid, nome in cursor.fetchall()}

    cursor.execute("""
        SELECT j.time_casa_id, j.time_fora_id, s.gols_casa, s.gols_fora, s.teve_shootout, s.vencedor_shootout
        FROM simulacoes s
        JOIN jogos j ON s.jogo_id = j.id
        WHERE s.usuario_id = %s
    """, (session['user_id'],))

    for casa, fora, gc, gf, shoot, vencedor in cursor.fetchall():
        times[casa]['j'] += 1
        times[fora]['j'] += 1
        times[casa]['gp'] += gc
        times[fora]['gp'] += gf
        times[casa]['gc'] += gf
        times[fora]['gc'] += gc
        times[casa]['sg'] = times[casa]['gp'] - times[casa]['gc']
        times[fora]['sg'] = times[fora]['gp'] - times[fora]['gc']

        if gc > gf:
            times[casa]['v'] += 1
            times[fora]['d'] += 1
            times[casa]['pts'] += 3
        elif gf > gc:
            times[fora]['v'] += 1
            times[casa]['d'] += 1
            times[fora]['pts'] += 3
        else:
            if shoot:
                if vencedor == 'casa':
                    times[casa]['v'] += 1
                    times[fora]['d'] += 1
                    times[casa]['pts'] += 2
                    times[fora]['pts'] += 1
                elif vencedor == 'fora':
                    times[fora]['v'] += 1
                    times[casa]['d'] += 1
                    times[fora]['pts'] += 2
                    times[casa]['pts'] += 1
            else:
                times[casa]['e'] += 1
                times[fora]['e'] += 1
                times[casa]['pts'] += 1
                times[fora]['pts'] += 1

    tabela = sorted(times.values(), key=lambda x: (-x['pts'], -x['sg'], -x['gp']))
    return render_template('tabela.html', tabela=tabela)

# ========== RUN APP ==========

if __name__ == '__main__':
    app.run(debug=True)
