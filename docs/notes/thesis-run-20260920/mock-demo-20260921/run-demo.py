"""Single-use local demonstration. Credentials live only in process memory/env."""
from pathlib import Path
import json,os,secrets,socket,subprocess,time,urllib.request

ROOT=Path.cwd()
OUT=ROOT/'tmp/continuation-20260921/demo-r3'
OUT.mkdir(parents=True,exist_ok=True)
MYSQL=Path('D:/Dev/mysql/bin')
JAVA=Path('D:/Dev/jdk21/bin/java.exe')
NODE=Path('C:/Users/can/AppData/Roaming/fnm/node-versions/v22.23.1/installation/node.exe')
PORTS=(3311,8081,4175)
children=[];handles=[]
report={'date':'2026-09-21','provider':'mock','database':'wrongbook_demo_20260921','ports':PORTS,'human_timing':False,'historical_database_used':False}
root_password=secrets.token_hex(24);db_password=secrets.token_hex(24)
def occupied(port):
    with socket.socket() as s:return s.connect_ex(('127.0.0.1',port))==0
def start(args,name,env=None,cwd=None):
    log=(OUT/(name+'.log')).open('wb');handles.append(log)
    p=subprocess.Popen([str(a) for a in args],cwd=cwd or ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    children.append((name,p));return p
def wait_port(port,process,timeout=80):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        if process.poll() is not None:raise RuntimeError('Process exited before readiness: '+str(port))
        if occupied(port):return
        time.sleep(.5)
    raise TimeoutError('Readiness timeout: '+str(port))
def sql(text,password=None):
    env=os.environ.copy()
    if password:env['MYSQL_PWD']=password
    else:env.pop('MYSQL_PWD',None)
    p=subprocess.run([str(MYSQL/'mysql.exe'),'--no-defaults','--host=127.0.0.1','--port=3311','--user=root','--default-character-set=utf8mb4','--batch','--skip-column-names'],input=text,encoding='utf-8',stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError('SQL operation failed (details intentionally not printed)')
    return p.stdout.strip()
try:
    if any(occupied(p) for p in PORTS):raise RuntimeError('Required port already occupied; no existing process stopped')
    data=OUT/'mysql-data'
    if data.exists():raise RuntimeError('Data directory already exists; refusing to reinitialize')
    init=subprocess.run([str(MYSQL/'mysqld.exe'),'--no-defaults','--initialize-insecure',f'--basedir={MYSQL.parent}',f'--datadir={data}'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    if init.returncode:raise RuntimeError('MySQL initialization failed')
    db=start([MYSQL/'mysqld.exe','--no-defaults',f'--basedir={MYSQL.parent}',f'--datadir={data}','--bind-address=127.0.0.1','--port=3311','--mysqlx=0','--console'],'mysql')
    wait_port(3311,db)
    sql(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{root_password}';")
    sql(f"CREATE DATABASE wrongbook_demo_20260921 CHARACTER SET utf8mb4; CREATE USER 'demo_app'@'localhost' IDENTIFIED BY '{db_password}'; GRANT ALL PRIVILEGES ON wrongbook_demo_20260921.* TO 'demo_app'@'localhost';",root_password)
    schema=(ROOT/'server/src/main/resources/db/schema.sql').read_text(encoding='utf-8')
    sql('USE wrongbook_demo_20260921;\n'+schema+"\nINSERT INTO subject(id,name,code) VALUES(1,'数学','math'); INSERT INTO knowledge_point(id,subject_id,parent_id,name) VALUES(1,1,0,'函数'),(2,1,1,'二次函数');",root_password)
    report['physical_tables']=int(sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='wrongbook_demo_20260921';",root_password))
    report['initial_users']=int(sql('SELECT COUNT(*) FROM wrongbook_demo_20260921.user;',root_password))
    env=os.environ.copy();env.update({'SPRING_PROFILES_ACTIVE':'deploy-test','SPRING_CONFIG_IMPORT':'','DEPLOY_TEST_PORT':'8081','DEPLOY_TEST_DB_URL':'jdbc:mysql://127.0.0.1:3311/wrongbook_demo_20260921?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai','DEPLOY_TEST_DB_USERNAME':'demo_app','DEPLOY_TEST_DB_PASSWORD':db_password,'DEPLOY_TEST_JWT_SECRET':secrets.token_hex(32),'DEPLOY_TEST_CORS_ORIGINS':'http://127.0.0.1:4175','DEPLOY_TEST_UPLOAD_DIR':str(OUT/'uploads'),'LLM_PROVIDER':'mock','IMAGE_RECOGNITION_ENABLED':'false','LLM_API_KEY':'','IMAGE_RECOGNITION_API_KEY':''})
    jar=next((ROOT/'server/target').glob('*.jar'))
    app=start([JAVA,'-jar',jar],'backend',env,ROOT/'server');wait_port(8081,app)
    for i in range(60):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8081/api/health',timeout=2) as response:report['health']=json.load(response)
            break
        except Exception:
            if i==59:raise
            time.sleep(.5)
    envweb=os.environ.copy();envweb['VITE_BACKEND_PROXY_TARGET']='http://127.0.0.1:8081'
    web=start([NODE,ROOT/'web/node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','4175','--strictPort'],'frontend',envweb,ROOT/'web');wait_port(4175,web)
    envbrowser=os.environ.copy();envbrowser.update({'DEMO_OUTPUT':str(OUT),'DEMO_PASSWORD':secrets.token_hex(12)})
    browser=start([NODE,ROOT/'tmp/continuation-20260921/demo-browser.mjs'],'browser',envbrowser)
    code=browser.wait(timeout=180);report['browser_exit']=code
    report['database_counts']=sql("USE wrongbook_demo_20260921; SELECT 'users',COUNT(*) FROM user UNION ALL SELECT 'questions',COUNT(*) FROM question UNION ALL SELECT 'analysis',COUNT(*) FROM ai_analysis UNION ALL SELECT 'variants',COUNT(*) FROM variant_question UNION ALL SELECT 'practice',COUNT(*) FROM practice_record UNION ALL SELECT 'review_plans',COUNT(*) FROM review_plan;",root_password)
    report['review_schedule']=sql("SELECT review_stage,plan_date,status FROM wrongbook_demo_20260921.review_plan;",root_password)
    report['passed']=code==0
except Exception as error:
    report['passed']=False;report['error']=str(error)
finally:
    for name,p in reversed(children):
        if p.poll() is None:
            if name=='mysql':
                try:sql('SHUTDOWN;',root_password)
                except Exception:pass
            else:p.terminate()
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    for handle in handles:handle.close()
    report['owned_processes_stopped']=all(p.poll() is not None for _,p in children)
    report['ports_closed']={str(p):not occupied(p) for p in PORTS}
    (OUT/'environment-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report.get('passed') else 1)
