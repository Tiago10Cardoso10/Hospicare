import hashlib
import uuid
from datetime import date, timedelta,datetime
import jwt
import logging
import psycopg2
import flask
import random
import os



from flask import request, jsonify, session
from datetime import timedelta

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'autenticacao'

StatusCodes = {  
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

def db_connection():
    try:
        conectar = psycopg2.connect(password='postgres', host='localhost', database='Hospicare', user='postgres')
        return conectar
    except psycopg2.DatabaseError as error:
        print(f"Error: {error}")
        return None

#       -------------------------------Main Functions-------------------------------        #

@app.route('/')
def projPage():
    return """
    Realizado Por:   <br/>
    <br/>
    Tiago Cardoso - 2021229679   <br/>
    <br/>
    Tomas Silva - 2021214124   <br/>
    <br/>
    """

@app.route('/Hospicare')
def landing_page():
    return """
    Bem-vindo!  <br/>
    <br/>
    Projeto BD 2024 <br/>
    <br/>
    """


# Inserir em user_information
def insert_user_info(nome, nacionalidade, genero, data_nascimento, email, telemovel, username, password):
    conn = db_connection()

    if conn is None:
        res = {'status':  StatusCodes['api_error'], 'error': 'Conexao com a base de dados falhou'}
        return None, res

    cur = conn.cursor()
    password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("LOCK TABLE user_information IN EXCLUSIVE MODE")

        cur.execute("""
            INSERT INTO user_information (nome, nacionalidade, genero, data_nascimento, email, telemovel, username, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING user_id
        """, (nome, nacionalidade, genero, data_nascimento, email, telemovel, username, password))
        
        user_id = cur.fetchone()[0]
        cur.execute("COMMIT")
        return user_id, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()
        conn.close()

# Inserir na tabela especifica
def insert_specific_user_table(user_id, user_type, extra_data):
    conn = db_connection()

    if conn is None:
        res = {'status': StatusCodes['api_error'], 'error': 'Conexao com a base de dados falhou'}
        return None, res

    cur = conn.cursor()
    try:
        if user_type != 'patient':
            contract_data_inicio = date.today()
            contract_data_fim = contract_data_inicio + timedelta(days=2*365)

            salario = 0
            if user_type == 'doctor':
                salario = 5000
            elif user_type == 'nurse':
                salario = 3000
            elif user_type == 'assistant':
                salario = 1500

            detalhes = "Contrato de 10h Diarias"

            cur.execute("BEGIN TRANSACTION")
            cur.execute("LOCK TABLE employee_contract IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO employee_contract (contract_data_inicio, contract_data_fim, contract_salario, contract_detalhes_contrato, user_information_user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (contract_data_inicio, contract_data_fim, salario, detalhes, user_id))

        cur.execute("BEGIN TRANSACTION")
        if user_type == 'doctor':
            cur.execute("LOCK TABLE doctor IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO doctor (employee_contract_user_information_user_id, med_licenca)
                VALUES (%s, %s)
            """, (user_id, extra_data['licenca']))

            # Adiciona as especializações
            for specialization in extra_data.get('especializacoes', []):
                specialization_id = verifica_especializacao(specialization)
                if specialization_id:
                    cur.execute("LOCK TABLE doctor_specialization IN EXCLUSIVE MODE")
                    cur.execute("""
                        INSERT INTO doctor_specialization (doctor_employee_contract_user_information_user_id, specialization_specialization_id)
                        VALUES (%s, %s)
                    """, (user_id, specialization_id))
        elif user_type == 'nurse':
            cur.execute("LOCK TABLE nurse IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO nurse (employee_contract_user_information_user_id, hier_valor, trabalho)
                VALUES (%s, %s, %s)
            """, (user_id, extra_data['hierarquia'], extra_data['role']))
        elif user_type == 'assistant':
            cur.execute("LOCK TABLE assistant IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO assistant (employee_contract_user_information_user_id)
                VALUES (%s)
            """, (user_id,))
        elif user_type == 'patient':
            cur.execute("LOCK TABLE patient IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO patient (user_information_user_id)
                VALUES (%s)
            """, (user_id,))
        cur.execute("COMMIT")
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()


@app.route('/Hospicare/register', methods=['GET'])
def register_page():
    return "Especificar o tipo de utilizador a registar: /patient, /nurse, /doctor, /assistant <br/>"

@app.route('/Hospicare/register/<user_type>', methods=['POST'])
def register_user(user_type):
    logger.info('POST /Hospicare/register/<user_type>')
    payload = request.get_json()

    nome = payload.get('nome')
    nacionalidade = payload.get('nacionalidade')
    genero = payload.get('genero')
    data_nascimento = payload.get('data_nascimento')
    email = payload.get('email')
    telemovel = payload.get('telemovel')
    username = payload.get('username')
    password = payload.get('password')

    missing_fields = []

    if not nome:
        missing_fields.append("nome")
    if not nacionalidade:
        missing_fields.append("nacionalidade")
    if genero not in ["Masculino", "Feminino", "Outro"]:
        missing_fields.append("genero (Masculino, Feminino, Outro)")
    if not data_nascimento:
        missing_fields.append("data_nascimento")
    if not email:
        missing_fields.append("email")
    if not telemovel:
        missing_fields.append("telemovel")
    if not username:
        missing_fields.append("username")
    if not password:
        missing_fields.append("password")

    extra_data = {}

    if user_type == 'doctor':
        licenca = payload.get('licenca')
        especializacoes = payload.get('especializacoes', [])
        if not licenca:
            missing_fields.append("licenca")
        extra_data['licenca'] = licenca
        extra_data['especializacoes'] = []
        if not especializacoes:
            missing_fields.append("especializacoes: []")
        for esp in especializacoes:
            extra_data['especializacoes'].append(esp)
    elif user_type == 'nurse':
        hierarquia = payload.get('hierarquia')
        role = payload.get('role', [])
        if not hierarquia:
            missing_fields.append("hierarquia")
        extra_data['hierarquia'] = hierarquia
        extra_data['role'] = []
        if not role:
            missing_fields.append("role: []")
        for esp in role:
            if esp not in ['Chefe-Principal', 'Chefe-Secundaria', 'Principal','Ajudante', 'Estagiaria']: 
                missing_fields.append("role (Chefe-Principal, Chefe-Secundaria, Principal, Ajudante, Estagiaria)")
                break
            else:
                extra_data['role'].append(esp)

    if missing_fields:
        logger.info('POST /Hospicare/register/<user_type> - Campos em falta')
        return jsonify({'status': StatusCodes['internal_error'], 'error': "Campos em falta: " + ", ".join(missing_fields)})
        
    user_id, error = insert_user_info(nome, nacionalidade, genero, data_nascimento, email, telemovel, username, password)
    if error:
        logger.info('POST /Hospicare/register/<user_type> - erro')
        return jsonify({'status': StatusCodes['internal_error'], 'error': error})

    success, error = insert_specific_user_table(user_id, user_type, extra_data)
    if not success:
        logger.info('POST /Hospicare/register/<user_type> - erro')
        return jsonify({'status': StatusCodes['internal_error'], 'error': error})

    logger.info('POST /Hospicare/register/<user_type> - Sucesso ao registar')
    return jsonify({'status': StatusCodes['success'], 'user_id': user_id})


#Autenticacão
@app.route('/Hospicare/user', methods=['PUT']) 
def autentica_utilizador():
    logger.info('PUT /Hospicare/user')
    auth = flask.request.authorization

    if not auth or not auth.username or not auth.password:
        response = {'status': StatusCodes['apiError'], 
                    'results': f'Username ou Password em falta'}
        return flask.jsonify(response)

    conn = db_connection()

    if conn is None:
        result = {'status': StatusCodes['api_error'], 'erro': 'Conexao a base de dados falhou'}
        return jsonify(result)

    cur = conn.cursor()

    result = None

    try:
        username = auth.username
        password = auth.password
        password = password.encode()
        password = hashlib.sha256(password).hexdigest()

        cur.execute("SELECT username, password FROM user_information WHERE username = %s", (username,))
        dados = cur.fetchone()

        if dados is not None:
            if dados[1] == password:
                session['logged_in'] = True

                token = jwt.encode({'username': dados[0]}, app.config['SECRET_KEY'])

                result = {'status': StatusCodes['success'], 'token': token}

                logger.info('PUT /Hospicare/user - Sucesso no Login')
                return jsonify(result)
            else:
                logger.info('PUT /Hospicare/user - Password nao corresponde')
                result = {'status': StatusCodes['internal_error'], 'erro': 'Password invalida'}

                return jsonify(result)
        else:
            logger.info('PUT /Hospicare/user - Username nao encontrado')
            result = {'status': StatusCodes['internal_error'], 'erro': 'Username nao encontrado'}
            return jsonify(result)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.info('PUT /Hospicare/user - erro')
        result = {'status': StatusCodes['internal_error'], 'erro': str(error)}
        cur.execute("ROLLBACK")

    finally:
        if conn is not None:
            cur.close()
            conn.close()

    return jsonify(result)

#criar consulta
@app.route('/Hospicare/appointment', methods=['POST']) 
def cria_appointment():
    logger.info('POST /Hospicare/appointment')
    payload = request.get_json()

    if not payload:
        logger.error('POST /Hospicare/appointment - Payload ausente')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Payload ausente'})
    
    token = flask.request.headers.get('x-access-tokens')
    if not token:
        logger.error('POST /Hospicare/appointment - Token de autenticação ausente - x-access-tokens')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticação ausente - x-access-tokens'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
    except jwt.ExpiredSignatureError:
        logger.error('POST /Hospicare/appointment - Token expirado')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token inválido'})

    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        # Verifica se é paciente
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('POST /Hospicare/appointment - Username nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})
        
        user_id = user[0]

        cur.execute("SELECT * FROM patient WHERE user_information_user_id = %s", (user_id,))
        patient = cur.fetchone()
        if patient is None:
            logger.info('POST /Hospicare/appointment - Nao e paciente')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Apenas pacientes podem criar agendamentos'})
        
        # Verifica campos obrigatórios no payload
        required_fields = ['data_marcada', 'hora_inicio', 'hora_final', 'tipo', 'sala_appointment', 'custo', 'doctor_id']
        missing_fields = [field for field in required_fields if field not in payload or not payload[field]]

        if missing_fields:
            logger.info('POST /Hospicare/appointment - Campos em falta')
            return jsonify({'status': StatusCodes['internal_error'], 'error': "Campos em falta: " + ", ".join(missing_fields)})

        # Verifica se o doctor_id existe
        doctor_id = payload['doctor_id']
        cur.execute("SELECT * FROM doctor WHERE employee_contract_user_information_user_id = %s", (doctor_id,))
        doctor = cur.fetchone()
        if doctor is None:
            logger.info('POST /Hospicare/appointment - Doctor_id nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Doctor_id nao encontrado'})
        
        try:
            data_marcada = datetime.strptime(payload['data_marcada'], '%d-%m-%Y').date()
            hora_inicio = float(payload['hora_inicio'].replace(':', '.'))
            hora_final = float(payload['hora_final'].replace(':', '.'))
        except ValueError as ve:
            logger.error(f'Erro de formatação nas datas ou horas: {ve}')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Formato de data ou hora invalido'})

        now = datetime.now()
        now_decimal = now.hour + now.minute / 100.0
        if data_marcada < now.date() or (data_marcada == now.date() and hora_inicio <= now_decimal):
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Nao e possivel marcar um agendamento para antes da data e hora atuais'})

        # Verifica se o médico não tem outro agendamento no mesmo horário
        cur.execute("""
            SELECT * FROM appointment 
            WHERE doctor_employee_contract_user_information_user_id = %s 
            AND data_marcada = %s 
            AND (hora_inicio < %s AND hora_final > %s)
        """, (doctor_id, data_marcada, hora_final, hora_inicio))

        doctor_appointments = cur.fetchone()
        if doctor_appointments:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'O medico ja possui um agendamento nesse horario'})

        # Cria uma nova bill
        cur.execute("BEGIN TRANSACTION")
        cur.execute("lock table bill in exclusive mode")
        cur.execute("INSERT INTO bill (custo_total) VALUES (%s) RETURNING bill_id", (payload['custo'],))
        bill_id = cur.fetchone()[0]
        
        # Insere o agendamento no banco de dados
        appointment_data = (
            data_marcada,
            hora_inicio,
            hora_final,
            payload['tipo'],
            payload['sala_appointment'],
            payload['custo'],
            bill_id,
            doctor_id,
            user_id
        )

        cur.execute("BEGIN TRANSACTION")
        cur.execute("lock appointment in exclusive mode")
        cur.execute("""
            INSERT INTO appointment 
            (data_marcada, hora_inicio, hora_final, tipo, sala_appointment, custo, bill_bill_id, doctor_employee_contract_user_information_user_id, patient_user_information_user_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING appointment_id
        """, appointment_data)
        appointment_id = cur.fetchone()[0]
        conn.commit()
        logger.info(f'POST /Hospicare/appointment - Sucesso ao agendar appointment {appointment_id}')
        return jsonify({'status': StatusCodes['success'], 'message': f'Agendamento criado com sucesso {appointment_id}'})
    
    except (Exception, psycopg2.DatabaseError) as error:
        conn.rollback()
        logger.error(f'Erro ao criar agendamento: {error}')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Erro ao criar agendamento'})
    
    finally:
        cur.close()
        conn.close()

#ver consultas
@app.route('/Hospicare/appointments/<int:patient_user_id>', methods=['GET'])
def get_appointments(patient_user_id):
    logger.info('GET /Hospicare/appointments/{}'.format(patient_user_id))
    token = flask.request.headers.get('x-access-tokens')

    if not token:
        return jsonify({'status':StatusCodes['api_error'], 'errors': 'Token de autenticação ausente'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
    except jwt.ExpiredSignatureError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token inválido'})

    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        # Verificar se o usuário é o próprio paciente ou um assistente
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('GET /Hospicare/appointments/{} - Usuario nao encontrado'.format(patient_user_id))
            return jsonify({'status':  StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})
        
        user_id = user[0]  # Assumindo que user_id é a primeira coluna
        
        # Verificar se o usuário é o paciente
        cur.execute("SELECT * FROM patient WHERE user_information_user_id = %s", (user_id,))
        patient = cur.fetchone()
        
        if not patient:
            # Verificar se o usuário é um assistente
            cur.execute("SELECT * FROM assistant WHERE employee_contract_user_information_user_id = %s", (user_id,))
            assistant = cur.fetchone()
            if not assistant:
                logger.info('GET /Hospicare/appointments/{} - Acesso nao autorizado'.format(patient_user_id))
                return jsonify({'status':  StatusCodes['api_error'], 'errors': 'Acesso não autorizado'})

        # Obter os agendamentos do paciente
        cur.execute("""
            SELECT a.appointment_id, a.data_marcada, a.hora_inicio, a.hora_final, a.tipo, a.sala_appointment, a.custo, a.bill_bill_id, 
            a.doctor_employee_contract_user_information_user_id, u.nome as doctor_name
            FROM appointment a
            JOIN user_information u ON a.doctor_employee_contract_user_information_user_id = u.user_id
            WHERE a.patient_user_information_user_id = %s
            ORDER BY a.data_marcada, a.hora_inicio
        """, (patient_user_id,))

        appointments = []
        rows = cur.fetchall()
        for row in rows:
            appointments.append({
                "id": row[0],
                "data": row[1],
                "hora_inicial": row[2],
                "hora_final": row[3],
                "tipo": row[4],
                "sala": row[5],
                "custo": row[6],
                "doctor_id": row[8],
                "Nome doctor": row[9]
            })

        if appointments != []:
            result = {
                'status':StatusCodes['success'] ,
                'results': appointments
            }
            logger.info('GET /Hospicare/appointments/ - Mostrado appointment com sucesso')
            return jsonify(result)
        else:
            result = {
                'status':StatusCodes['success'] ,
                'results': "Nao tem appointments marcados"
            }
            logger.info('GET /Hospicare/appointments/ - Mostrado appointment com sucesso')
            return jsonify(result)

    except Exception as e:
        conn.rollback()
        logger.error(f'Erro ao obter agendamentos: {e}')
        return jsonify({'status': StatusCodes['internal_error'], 'errors': str(e)})

    finally:
        cur.close()
        conn.close()

#criar cirurgia
@app.route('/Hospicare/surgery', methods=['POST'])
@app.route('/Hospicare/surgery/<int:hospitalization_id>', methods=['POST']) 
def cria_surgery(hospitalization_id=None):
    logger.info('POST /Hospicare/surgery')
    payload = request.get_json()

    if not payload:
        logger.error('POST /Hospicare/surgery - Payload ausente')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Payload ausente'})

    token = flask.request.headers.get('x-access-tokens')
    if not token:
        logger.error('POST /Hospicare/surgery - Token de autenticação ausente - x-access-tokens')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticacao ausente - x-access-tokens'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
    except jwt.ExpiredSignatureError:
        logger.error('POST /Hospicare/surgery - Token expirado')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token invalido'})

    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        # Verifica se é assistant
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('POST /Hospicare/surgery - Username nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})
        
        assistant_id = user[0]

        cur.execute("SELECT * FROM assistant WHERE employee_contract_user_information_user_id = %s", (assistant_id,))
        assistant = cur.fetchone()
        if assistant is None:
            logger.info('POST /Hospicare/surgery - Nao e assistente')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Apenas assistente podem criar cirurgias'})

        # Verifica campos obrigatórios no payload
        required_fields = ['data_marcada', 'hora_inicio', 'hora_final', 'sala_surgery', 'tipo', 'doctor_id', 'nurses', 'user_id']
        missing_fields = [field for field in required_fields if field not in payload or not payload[field]]

        if missing_fields:
            logger.info('POST /Hospicare/surgery - Campos em falta')
            return jsonify({'status': StatusCodes['internal_error'], 'errors': "Campos em falta: " + ", ".join(missing_fields)})

        # Verifica se o doctor_id existe
        doctor_id = payload['doctor_id']
        cur.execute("SELECT * FROM doctor WHERE employee_contract_user_information_user_id = %s", (doctor_id,))
        doctor = cur.fetchone()
        if doctor is None:
            logger.info('POST /Hospicare/surgery - Doctor_id nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Doctor_id nao encontrado'})
        
        try:
            data_marcada = datetime.strptime(payload['data_marcada'], '%d-%m-%Y').date()
            hora_inicio = float(payload['hora_inicio'].replace(':', '.'))
            hora_final = float(payload['hora_final'].replace(':', '.'))
        except ValueError as ve:
            logger.error(f'Erro de formatação nas datas ou horas: {ve}')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Formato de data ou hora invalido'})

        now = datetime.now()
        now_decimal = now.hour + now.minute / 100.0
        if data_marcada < now.date() or (data_marcada == now.date() and hora_inicio <= now_decimal):
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Nao e possivel marcar um agendamento para antes da data e hora atuais'})

        # Verifica se o médico não tem outro agendamento no mesmo horário
        cur.execute("""
            SELECT * FROM appointment 
            WHERE doctor_employee_contract_user_information_user_id = %s 
            AND data_marcada = %s 
            AND (hora_inicio < %s AND hora_final > %s)
        """, (doctor_id, data_marcada, hora_final, hora_inicio))

        doctor_appointments = cur.fetchone()
        if doctor_appointments:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'O medico ja possui um agendamento nesse horario'})


        # Verifica se os nurse_ids existem
        try:
            nurse_ids = [int(nurse[0]) for nurse in payload['nurses']]
        except (ValueError, IndexError):
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Nurse_id(s) invalido(s)'})

        for nurse_id in nurse_ids:
            cur.execute("SELECT * FROM nurse WHERE employee_contract_user_information_user_id = %s", (nurse_id,))
            nurse = cur.fetchone()
            if nurse is None:
                logger.info(f'POST /Hospicare/surgery - Nurse_id {nurse_id} nao encontrado')
                return jsonify({'status': StatusCodes['api_error'], 'errors': f'Nurse_id {nurse_id} nao encontrado'})


        # Verifica se os enfermeiros não têm mais de uma hospitalização ao mesmo tempo
        for nurse_id in nurse_ids:
            cur.execute("""
                SELECT COUNT(*) FROM nurse_surgery ns
                JOIN surgery s ON ns.surgery_surgery_id = s.surgery_id
                WHERE ns.nurse_employee_contract_user_information_user_id = %s
                AND s.data_marcada = %s AND (
                    (s.hora_inicio <= %s AND s.hora_final >= %s) OR
                    (s.hora_inicio <= %s AND s.hora_final >= %s) OR
                    (s.hora_inicio >= %s AND s.hora_final <= %s)
                )
            """, (nurse_id, data_marcada, hora_inicio, hora_inicio, hora_final, hora_final, hora_inicio, hora_final))
            nurse_conflict = cur.fetchone()[0]
            if nurse_conflict > 0:
                return jsonify({'status': StatusCodes['api_error'], 'errors': f'Enfermeiro {nurse_id} já tem uma cirurgia marcada para esse horário'})

        cur.execute("BEGIN TRANSACTION")

        # Se hospitalization_id não for fornecido, cria uma nova hospitalização
        if not hospitalization_id:
            if 'quarto' not in payload:
                logger.info('POST /Hospicare/surgery - Campo "quarto" em falta')
                return jsonify({'status': StatusCodes['internal_error'], 'errors': 'Campo "quarto" em falta'})

            # Cria a fatura se o custo for fornecido
            if 'custo' not in payload:
                logger.info('POST /Hospicare/surgery - Campo "custo" em falta')
                return jsonify({'status': StatusCodes['internal_error'], 'errors': 'Campo "custo" em falta'})
            
            cur.execute("LOCK TABLE bill IN EXCLUSIVE MODE")
            cur.execute("INSERT INTO bill (custo_total) VALUES (%s) RETURNING bill_id", (payload['custo'],))
            bill_id = cur.fetchone()[0]

            # Cria a hospitalização
            cur.execute("LOCK TABLE hospitalization IN EXCLUSIVE MODE")
            cur.execute("""
                INSERT INTO hospitalization (data_entrada, data_saida, tipo, quarto, custo, bill_bill_id, nurse_employee_contract_user_information_user_id, patient_user_information_user_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING hospitalization_id
            """, (now.date(), now.date() + timedelta(days=3), "Cirurgia", payload['quarto'], payload['custo'], bill_id, nurse_ids[0], payload['user_id']))

            hospitalization_id = cur.fetchone()[0]

        # Insere a cirurgia no banco de dados
        surgery_data = (
            data_marcada,
            hora_inicio,
            hora_final,
            payload['sala_surgery'],
            payload['tipo'],
            payload['custo'],
            hospitalization_id,
            doctor_id
        )

        cur.execute("LOCK TABLE surgery IN EXCLUSIVE MODE")
        cur.execute("""
            INSERT INTO surgery 
            (data_marcada, hora_inicio, hora_final, sala_surgery, tipo, custo, hospitalization_hospitalization_id, doctor_employee_contract_user_information_user_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING surgery_id
        """, surgery_data)

        surgery_id = cur.fetchone()[0]

        # Retrieve hospitalization_id associated with the surgery
        cur.execute("SELECT hospitalization_hospitalization_id FROM surgery WHERE surgery_id = %s", (surgery_id,))
        hospitalization_id = cur.fetchone()[0]

        # Associa os enfermeiros à cirurgia
        cur.execute("LOCK TABLE nurse_surgery IN EXCLUSIVE MODE")
        for nurse_id in nurse_ids:
            cur.execute("INSERT INTO nurse_surgery (surgery_surgery_id, nurse_employee_contract_user_information_user_id, surgery_hospitalization_hospitalization_id) VALUES (%s, %s, %s)", (surgery_id, nurse_id, hospitalization_id))

        cur.execute("COMMIT")

        return jsonify({'status': StatusCodes['success'], 'message': 'Cirurgia criada com sucesso', 'surgery_id': surgery_id})

    except Exception as e:
        conn.rollback()
        logger.error(f'Erro ao criar cirurgia: {e}')
        return jsonify({'status': StatusCodes['api_error'], 'errors': str(e)})

    finally:
        cur.close()
        conn.close()

#ver precriçoes
@app.route('/Hospicare/prescriptions/<int:person_id>', methods=['GET'])
def get_prescriptions(person_id):
    logger.info('GET /Hospicare/prescriptions/<int:person_id>')
    token = flask.request.headers.get('x-access-tokens')
    if not token:
        logger.error('Token de autenticação ausente - x-access-tokens')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticacao ausente'}), 401

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
    except jwt.ExpiredSignatureError:
        logger.error('Token expirado')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        logger.error('Token inválido')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token invalido'}), 401

    conn = db_connection()
    if conn is None:
        logger.error('Conexão com a base de dados falhou')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'}), 500

    cur = conn.cursor()

    try:
        # Verificar se o current_user é o próprio paciente ou um funcionário
        cur.execute("""
            SELECT * FROM user_information 
            WHERE user_id = %s AND username = %s
            UNION
            SELECT user_information.* 
            FROM user_information
            JOIN employee_contract ON user_information.user_id = employee_contract.user_information_user_id
            WHERE user_information.username = %s
        """, (person_id, current_user, current_user))
        user_check = cur.fetchone()

        if not user_check:
            logger.error('Acesso não autorizado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Acesso nao autorizado'}), 403

        # Buscar os IDs de consulta associados ao paciente nas tabelas appointments e hospitalization
        cur.execute("""
            SELECT appointment_id FROM appointment WHERE patient_user_information_user_id = %s
            UNION
            SELECT hospitalization_id FROM hospitalization WHERE patient_user_information_user_id = %s
        """, (person_id, person_id))
        consulta_ids = [row[0] for row in cur.fetchall()]

        prescriptions = []
        for consulta_id in consulta_ids:
            # Buscar prescrições associadas ao ID de consulta na tabela prescription_appointment
            cur.execute("""
                SELECT prescription_prescricao_id FROM prescription_appointment WHERE appointment_appointment_id = %s
            """, (consulta_id,))
            prescricao_ids = [row[0] for row in cur.fetchall()]

            for prescricao_id in prescricao_ids:
                # Buscar detalhes das prescrições na tabela prescription
                cur.execute("""
                    SELECT * FROM prescription WHERE prescricao_id = %s
                """, (prescricao_id,))
                prescription_data = cur.fetchone()

                # Buscar os efeitos colaterais associados à prescrição
                cur.execute("""
                    SELECT mse.side_effect_effects_id, mse.tipo, mse.side_effect_sintomas, mse.side_effect_probabiilidade
                    FROM medication_side_effect_prescription msep
                    JOIN medication_side_effect mse ON msep.medication_side_effect_medication_id = mse.medication_id
                    WHERE msep.prescription_prescricao_id = %s
                """, (prescricao_id,))
                medication = cur.fetchone()

                prescription = {
                    "prescription_id": prescription_data[0],
                    "data_inicial": prescription_data[1],
                    "data_final": prescription_data[2],
                    "medicacao": {
                        "medicine_name": medication[1] if medication else None,  
                        "dose": prescription_data[3],
                        "side_effects": [
                            {
                                "sintomas": medication[2] if medication else None,
                                "probabilidade": medication[3] if medication else None
                            }
                        ] if medication else []
                    }
                }

                prescriptions.append(prescription)

        if not prescriptions:
            result = {
                'status': StatusCodes['success'],
                'results': "Nao existem prescriptions ainda"
            }
        else:
            result = {
                'status': StatusCodes['success'],
                'results': prescriptions
            }

        logger.info('Prescrições mostradas com sucesso')
        return jsonify(result)

    except Exception as e:
        logger.error(f'Erro ao mostrar prescrições: {e}')
        return jsonify({'status': StatusCodes['internal_error'], 'errors': str(e)}), 500

    finally:
        cur.close()
        conn.close()


#criar uma prescription
@app.route('/Hospicare/prescription/', methods=['POST'])
def adicionar_prescricao():
    logger.info('POST /Hospicare/prescription/')
    payload = request.get_json()

    if not payload:
        logger.error('POST /Hospicare/prescription/ - Payload ausente')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Payload ausente'})
    
    token = flask.request.headers.get('x-access-tokens')
    if not token:
        logger.error('POST /Hospicare/prescription/ - Token de autenticacao ausente - x-access-tokens')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticacao ausente - x-access-tokens'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
        
        # Verifica se o usuário é um doctor
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('POST /Hospicare/appointment - Username nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})
        
        user_id = user[0]  # Assumindo que user_id é a primeira coluna

        cur.execute("SELECT * FROM doctor WHERE employee_contract_user_information_user_id = %s", (user_id,))
        doctor = cur.fetchone()
        if doctor is None:
            logger.error('POST /Hospicare/prescription/ - Apenas medicos podem criar prescription')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Apenas medicos podem criar prescription'})

    except jwt.ExpiredSignatureError:
        logger.error('POST /Hospicare/prescription/ - Token expirado')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        logger.error('POST /Hospicare/prescription/ - Token invalido')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token invalido'})
    finally:
        cur.close()
        conn.close()

    # Verificar campos obrigatórios no payload
    required_fields = ['data_inicial', 'data_final', 'quantidade']
    missing_fields = [field for field in required_fields if field not in payload or not payload[field]]
    if missing_fields:
        logger.error('POST /Hospicare/prescription/ - Campos obrigatorios ausentes no payload')
        return jsonify({'status': StatusCodes['api_error'], 'errors': f'Campos obrigatorios ausentes no payload: {missing_fields}'})

    # Verificar se a prescrição está associada a uma consulta ou hospitalização válida
    appointment_id = payload.get('appointment')
    hospitalization_id = payload.get('hospitalization')

    if not appointment_id and not hospitalization_id:
        logger.error('POST /Hospicare/prescription/ - Prescricao deve estar associada a uma consulta ou hospitalizacao')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Prescricao deve estar associada a uma consulta ou hospitalizacao - hospitalization,appointment'})
    
    # Verificar se a consulta ou hospitalização existe
    if appointment_id:
        appointment_exists = verificar_appointment(appointment_id)
        if not appointment_exists:
            logger.error('POST /Hospicare/prescription/ - ID appointment invalido')
            return jsonify({'status': StatusCodes['api_error'], 'errors': ' ID appointment invalido'})

    if hospitalization_id:
        hospitalization_exists = verificar_hospitalization(hospitalization_id)
        if not hospitalization_exists:
            logger.error('POST /Hospicare/prescription/ - ID hospitalization invalido')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'ID hospitalization invalido'})

    # Se todas as verificações passarem, você pode prosseguir com a adição da prescrição
    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        
        cur.execute("BEGIN TRANSACTION")
        cur.execute("lock prescription in exclusive mode")
        cur.execute("INSERT INTO prescription (data_inical, data_final, quantidade) VALUES (%s, %s, %s) RETURNING prescricao_id", 
                    (payload['data_inicial'], payload['data_final'], payload['quantidade']))
        prescription_id = cur.fetchone()[0]

        if appointment_id:
            cur.execute("lock prescription_appointment in exclusive mode")
            cur.execute("INSERT INTO prescription_appointment (prescription_prescricao_id, appointment_appointment_id) VALUES (%s, %s)", 
                        (prescription_id, appointment_id))
        
        if hospitalization_id:
            cur.execute("lock prescription_hospitalization in exclusive mode")
            cur.execute("INSERT INTO prescription_hospitalization (prescription_prescricao_id, hospitalization_hospitalization_id) VALUES (%s, %s)", 
                        (prescription_id, hospitalization_id))


        medications = payload.get('medications', [])
        if not medications:
            logger.error('POST /Hospicare/prescription/ - Campos obrigatórios ausentes no payload: medications[]')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Campos obrigatorios ausentes no payload: medications[]'})

        for medication in medications:
            medication_id = medication.get('medication_id')
            existing_medication_id = verifica_medication(medication_id)

            if existing_medication_id is None:
                
                tipo = medication.get('tipo')
                sintomas = medication.get('sintomas')
                probabilidade = medication.get('probabilidade')

                if not (tipo and sintomas and probabilidade):
                    logger.error('POST /Hospicare/prescription/ - Campos obrigatorios ausentes no payload para medicacao - tipo,sintomas,probalilidade')
                    return jsonify({'status': StatusCodes['api_error'], 'errors': 'Campos obrigatorios ausentes no payload para medicacao - tipo,sintomas,probalilidade'})

                # Agora que temos certeza de que os campos estão presentes e não são nulos,
                # podemos proceder com a inserção da medicação
                try:
                    cur.execute("INSERT INTO medication_side_effect (tipo, side_effect_sintomas, side_effect_probabiilidade) VALUES (%s, %s, %s) RETURNING medication_id", 
                                (tipo, sintomas, probabilidade))
                    existing_medication_id = cur.fetchone()[0]
                except (Exception, psycopg2.DatabaseError) as error:
                    logger.error(f'POST /Hospicare/prescription/ - Erro ao adicionar medicação: {error}')
                    conn.rollback()
                    return jsonify({'status': StatusCodes['api_error'], 'errors': 'Erro ao adicionar medicacao'})

            # Agora que temos certeza de que a medicação existe ou foi adicionada com sucesso,
            # podemos associá-la à prescrição
            try:
                cur.execute("INSERT INTO medication_side_effect_prescription (medication_side_effect_medication_id, prescription_prescricao_id) VALUES (%s, %s)", 
                            (existing_medication_id, prescription_id))
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(f'POST /Hospicare/prescription/ - Erro ao associar medicacao a prescricao: {error}')
                conn.rollback()
                return jsonify({'status': StatusCodes['api_error'], 'errors': 'Erro ao associar medicacao a prescricao'})


        cur.execute("lock prescription in exclusive mode")
        cur.execute("INSERT INTO prescription (data_inical, data_final, quantidade) VALUES (%s, %s, %s) RETURNING prescricao_id", 
                    (payload['data_inicial'], payload['data_final'], payload['quantidade']))
        prescription_id = cur.fetchone()[0]

        if appointment_id:
            cur.execute("lock prescription_appointment in exclusive mode")
            cur.execute("INSERT INTO prescription_appointment (prescription_prescricao_id, appointment_appointment_id) VALUES (%s, %s)", 
                        (prescription_id, appointment_id))
        
        if hospitalization_id:
            cur.execute("lock prescription_hospitalization in exclusive mode")
            cur.execute("INSERT INTO prescription_hospitalization (prescription_prescricao_id, hospitalization_hospitalization_id) VALUES (%s, %s)", 
                        (prescription_id, hospitalization_id))

        conn.commit()
        logger.info('POST /Hospicare/prescription/ - Prescricao adicionada com sucesso')
        return jsonify({'status': StatusCodes['success'], 'prescription_id': prescription_id})
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /Hospicare/prescription/ - Erro ao adicionar prescricao: {error}')
        conn.rollback()
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Erro ao adicionar prescricao'})
    finally:
        cur.close()
        conn.close()

@app.route('/Hospicare/bills/<int:bill_id>', methods=['POST'])
def executar_pagamento(bill_id):
    logger.info('POST /Hospicare/bills/<int:bill_id>')
    payload = request.get_json()

    if not payload:
        logger.error('POST /Hospicare/bills/<int:bill_id> - Payload ausente')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Payload ausente'})
    
    token = flask.request.headers.get('x-access-tokens')
    if not token:
        logger.error('POST /Hospicare/prescription/ - Token de autenticacao ausente - x-access-tokens')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticacao ausente -  '})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
        
        # Verifica se o usuário é um paciente
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('POST /Hospicare/appointment - Username nao encontrado')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})
        
        user_id = user[0]  # Assumindo que user_id é a primeira coluna

        cur.execute("SELECT * FROM patient WHERE user_information_user_id = %s", (user_id,))
        doctor = cur.fetchone()
        if doctor is None:
            logger.error('POST /Hospicare/prescription/ - Apenas pacientes podem fazer pagamentos')
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Apenas pacientes podem fazer pagamentos'})

    except jwt.ExpiredSignatureError:
        logger.error('POST /Hospicare/prescription/ - Token expirado')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        logger.error('POST /Hospicare/prescription/ - Token invalido')
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token invalido'})
    finally:
        cur.close()
        conn.close()


    # Verificar campos obrigatórios no payload
    required_fields = ['quantidade', 'data_maxima', 'forma_pagamento']
    missing_fields = [field for field in required_fields if field not in payload or not payload[field]]
    if missing_fields:
        logger.error('POST /Hospicare/prescription/ - Campos obrigatorios ausentes no payload')
        return jsonify({'status': StatusCodes['api_error'], 'errors': f'Campos obrigatorios ausentes no payload: {missing_fields}'})

    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        
        cur.execute("SELECT * FROM appointment WHERE bill_bill_id = %s", (bill_id,))
        appointments = cur.fetchall()

        cur.execute("SELECT * FROM hospitalization WHERE bill_bill_id = %s", (bill_id,))
        hospitalizations = cur.fetchall()

        
        events = appointments + hospitalizations

        # Se nenhum evento for encontrado, retorna um erro
        if not events:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Nenhum bill com esse id'})

        
        cur.execute("SELECT custo_total FROM bill WHERE bill_id = %s", (bill_id,))
        bill_total = cur.fetchone()

        # Verifica se o valor total foi encontrado
        if not bill_total:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Nao existe uma bill com esse id na tabela bill'})

        bill_total = bill_total[0]  # custo_total é a primeira coluna

        if bill_total == 0:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Esta bill esta paga'})

        # Verifica se o valor total dos eventos é maior que o valor total 
        if float(payload['quantidade']) > bill_total:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'O valor e maior que o existente:'}) # Dizer existente

        # Verifica se o pagamento é maior que zero
        if float(payload['quantidade']) < 0:
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'O pagamento nao pode ser com valor negativo'})
        
        
            
        remaining_balance = bill_total - float(payload['quantidade'])
        cur.execute("LOCK TABLE payment IN EXCLUSIVE MODE")
        # Insere os dados na tabela payment
        cur.execute("INSERT INTO payment (quantidade, data_maxima, forma_pagamento, bill_bill_id) VALUES (%s, %s, %s, %s)",
                    (payload['quantidade'], payload['data_maxima'], payload['forma_pagamento'], bill_id))
        conn.commit()

        cur.execute("LOCK TABLE bill IN EXCLUSIVE MODE")
        # Atualiza o valor_total do projeto de lei na base de dados
        cur.execute("UPDATE bill SET custo_total = %s WHERE bill_id = %s", (remaining_balance, bill_id))
        conn.commit()

        
        cur.close()
        conn.close()

        # Retorna o valor restante da conta em caso de sucesso
        return jsonify({'status': StatusCodes['success'], 'remaining_balance': remaining_balance})

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /Hospicare/bills/<int:bill_id> - Erro ao executar pagamento: {error}')
        conn.rollback()
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Erro ao executar pagamento'})
    finally:
        cur.close()
        conn.close()



@app.route('/Hospicare/daily/<string:date>', methods=['GET']) 
def daily_summary(date):
    logger.info('GET /Hospicare/daily/{}'.format(date))
    token = flask.request.headers.get('x-access-tokens')

    if not token:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token de autenticação ausente'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = data['username']
    except jwt.ExpiredSignatureError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token expirado'})
    except jwt.InvalidTokenError:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Token invalido'})

    conn = db_connection()
    if conn is None:
        return jsonify({'status': StatusCodes['api_error'], 'errors': 'Conexao com a base de dados falhou'})

    cur = conn.cursor()

    try:
        # Verificar se o usuário é um assistente
        cur.execute("SELECT * FROM user_information WHERE username = %s", (current_user,))
        user = cur.fetchone()
        if user is None:
            logger.info('GET /Hospicare/daily/{} - Usuario não encontrado'.format(date))
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Usuario nao encontrado'})

        user_id = user[0]  # Assumindo que user_id é a primeira coluna
        
        cur.execute("SELECT * FROM assistant WHERE employee_contract_user_information_user_id = %s", (user_id,))
        assistant = cur.fetchone()
        if not assistant:
            logger.info('GET /Hospicare/daily/{} - Acesso não autorizado'.format(date))
            return jsonify({'status': StatusCodes['api_error'], 'errors': 'Acesso não autorizado'})

        # Executar a consulta para obter o resumo diário
        cur.execute("""
            SELECT 
                COALESCE(SUM(b.custo_total), 0) AS amount_spent,
                (SELECT COUNT(DISTINCT s.surgery_id) 
                FROM surgery s 
                WHERE s.data_marcada = %s) AS surgeries,
                (SELECT COUNT(DISTINCT p.prescricao_id) 
                FROM prescription p 
                WHERE p.data_inical = %s) AS prescriptions
            FROM bill b
            LEFT JOIN hospitalization h ON b.bill_id = h.bill_bill_id
            LEFT JOIN appointment a ON b.bill_id = a.bill_bill_id
            WHERE h.data_entrada = %s OR a.data_marcada = %s
        """, (date, date, date, date))

        summary = cur.fetchone()
        result = {
            'status': StatusCodes['success'],
            'results': {
                'amount_spent': summary[0],
                'surgeries': summary[1],
                'prescriptions': summary[2]
            }
        }
        return jsonify(result)

    except Exception as e:
        conn.rollback()
        logger.error(f'Erro ao obter resumo diario: {e}')
        return jsonify({'status': StatusCodes['internal_error'], 'errors': str(e)})

    finally:
        cur.close()
        conn.close()


#       --------Auxiliary Functions--------      #

def verifica_medication(medication_id):
    conn = db_connection()
    cur = conn.cursor()

    try:
        # Verificar se o ID da medicação existe na tabela medication_side_effect
        cur.execute("SELECT * FROM medication_side_effect WHERE medication_id = %s", (medication_id,))
        result = cur.fetchone()

        if result is None:
            # O ID da medicação não existe
            return None
        else:
            return result[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Erro ao verificar/inserir efeito colateral: {error}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def verificar_appointment (appointment_id):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM appointment WHERE appointment_id = %s", (appointment_id,))
    appointment = cur.fetchone()
    cur.close()
    conn.close()
    return appointment is not None

def verificar_hospitalization(hospitalization_id):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospitalization WHERE hospitalization_id = %s", (hospitalization_id,))
    hospitalization = cur.fetchone()
    cur.close()
    conn.close()
    return hospitalization is not None

def verifica_username(nome):
    conn = db_connection()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT nome FROM user_information WHERE username = %s", (nome,))
        res = cur.fetchall()
        return len(res) > 0
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'erro: {error}')
        return False
    finally:
        if conn is not None:
            cur.close()
            conn.close()

def verifica_email(email):
    conn = db_connection()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM user_information WHERE email = %s", (email,))
        res = cur.fetchall()
        return len(res) > 0
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'erro: {error}')
        return False
    finally:
        if conn is not None:
            cur.close()
            conn.close()

def verifica_telemovel(telemovel):
    conn = db_connection()
    if conn is None:
        return False
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM user_information WHERE telemovel = %s", (telemovel,))
        res = cur.fetchall()
        return len(res) > 0
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'erro: {error}')
        return False
    finally:
        if conn is not None:
            cur.close()
            conn.close()

def verifica_especializacao(specialization_tipo):
    conn = db_connection()
    if conn is None:
        return False
    
    cur = conn.cursor()
    
    try:
        # Verifica se a especialização já existe na tabela
        cur.execute("SELECT specialization_id FROM specialization WHERE tipo = %s", (specialization_tipo,))
        existing_specialization = cur.fetchone()

        if existing_specialization:
            # Se a especialização já existe, retorna o ID da especialização
            specialization_id = existing_specialization[0]
        else:
            # Se a especialização não existe, insere na tabela e retorna o ID gerado
            cur.execute("INSERT INTO specialization (tipo) VALUES (%s) RETURNING specialization_id", (specialization_tipo,))
            specialization_id = cur.fetchone()[0]
            conn.commit()

        cur.close()
        return specialization_id
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'erro: {error}')
        return None
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}')
