#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

HARNESS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(HARNESS_DIR, "harness.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def generate_report():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Stats Generales
    decisions_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    lessons_count = conn.execute("SELECT COUNT(*) FROM lessons_learned").fetchone()[0]
    resources_count = conn.execute("SELECT COUNT(*) FROM resource_registry").fetchone()[0]
    
    # 2. Agent Activity Ranking
    activity = conn.execute("""
        SELECT agent, COUNT(*) as count 
        FROM agent_activity_log 
        GROUP BY agent 
        ORDER BY count DESC
    """).fetchall()
    
    # 3. Validation Health
    health = conn.execute("""
        SELECT validation_status, COUNT(*) as count 
        FROM resource_registry 
        GROUP BY validation_status
    """).fetchall()
    
    # 4. Critical Lessons
    critical_lessons = conn.execute("""
        SELECT title, agent FROM lessons_learned WHERE severity = 'critical'
    """).fetchall()
    
    conn.close()

    # Construir Markdown
    md = [
        f"# 📊 Harness Engineering — Health Report",
        f"> Generado el: **{now}**\n",
        f"Este reporte es generado automáticamente por la capa de Analytics de HarnessDB para medir la madurez y estabilidad del sistema.\n",
        f"## 📈 Métricas Globales",
        f"- **Decisiones Arquitectónicas:** {decisions_count}",
        f"- **Lecciones Aprendidas:** {lessons_count}",
        f"- **Recursos K8s Rastreados:** {resources_count}\n",
        f"## 🤖 Actividad de Agentes",
        f"Ranking de intervenciones automatizadas en el repositorio:\n"
    ]
    
    for row in activity:
        md.append(f"- **{row['agent']}**: {row['count']} acciones")
        
    md.append("\n## 🏥 Estado del Clúster (Última Validación)")
    for row in health:
        status = row['validation_status']
        icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌" if status == "error" else "⚪"
        md.append(f"- {icon} **{status.capitalize()}**: {row['count']} recursos")
        
    if critical_lessons:
        md.append("\n## 🔴 Alertas Críticas (Lessons Learned)")
        for row in critical_lessons:
            md.append(f"- {row['title']} (Descubierto por: {row['agent']})")
            
    return "\n".join(md)

def main():
    if not os.path.exists(DB_PATH):
        print("❌ Error: harness.db no existe.")
        return
        
    report_md = generate_report()
    
    # Escribir a la raíz del proyecto
    project_root = os.path.dirname(HARNESS_DIR)
    out_path = os.path.join(project_root, "STATUS.md")
    
    with open(out_path, "w") as f:
        f.write(report_md)
        
    print(f"✅ Reporte generado exitosamente en: {out_path}")

if __name__ == "__main__":
    main()
