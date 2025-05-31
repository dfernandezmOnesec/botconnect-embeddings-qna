import streamlit as st
import pandas as pd
import datetime
import random

# Datos de ejemplo (en una aplicación real vendrían de una base de datos)
eventos = [
    {"id": 1, "nombre": "Retiro Espiritual", "fecha": datetime.date(2023, 11, 15), "lugar": "Sede Principal", "descripcion": "Un fin de semana para renovar tu espíritu y conectar con Dios"},
    {"id": 2, "nombre": "Concierto de Alabanza", "fecha": datetime.date(2023, 12, 10), "lugar": "Auditorio Central", "descripcion": "Noche de adoración con artistas invitados"},
    {"id": 3, "nombre": "Campamento Juvenil", "fecha": datetime.date(2023, 12, 28), "lugar": "Centro de Retiros", "descripcion": "Evento para jóvenes de 13 a 18 años"}
]

ministerios = [
    {"id": 1, "nombre": "Alabanza y Adoración", "responsable": "Pastor Carlos", "contacto": "alabanza@comunidad.org"},
    {"id": 2, "nombre": "Misiones", "responsable": "Hna. María", "contacto": "misiones@comunidad.org"},
    {"id": 3, "nombre": "Escuela Dominical", "responsable": "Hno. Javier", "contacto": "escuela@comunidad.org"}
]

personal = [
    {"id": 1, "nombre": "Pastor Juan Pérez", "cargo": "Pastor Principal", "contacto": "pastorjuan@comunidad.org"},
    {"id": 2, "nombre": "Hermana Luisa Gómez", "cargo": "Administración", "contacto": "luisa@comunidad.org"},
    {"id": 3, "nombre": "Hermano Miguel Torres", "cargo": "Ministerio de Jóvenes", "contacto": "miguel@comunidad.org"}
]

# Configuración de la página
st.set_page_config(
    page_title="Comunidad de Fe",
    page_icon="⛪",
    layout="wide",
    menu_items={
        'Obtener ayuda': 'mailto:soporte@comunidad.org',
        'Reportar un problema': 'mailto:soporte@comunidad.org',
        'Acerca de': '''
        ## Comunidad de Fe
        Plataforma para conectar, servir y crecer juntos en la fe.
        '''
    }
)

# Estilos personalizados
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .header {
        background-color: #4b6cb7;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .section {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .event-card {
        border-left: 4px solid #4b6cb7;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f0f4ff;
        border-radius: 0 8px 8px 0;
    }
    .contact-card {
        display: flex;
        align-items: center;
        padding: 15px;
        border-bottom: 1px solid #eee;
    }
    .contact-card img {
        border-radius: 50%;
        margin-right: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<div class="header"><h1>Comunidad de Fe</h1><p>Conectando corazones, sirviendo con amor</p></div>', unsafe_allow_html=True)

# Menú de secciones
seccion = st.sidebar.radio("Navegación", ["🏠 Inicio", "📅 Eventos", "💖 Donaciones", "👥 Directorio", "📞 Contacto"])

# Página de Inicio
if seccion == "🏠 Inicio":
    st.markdown('<div class="section"><h2>Bienvenidos a nuestra comunidad</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="section">
            <h3>Próximos Eventos</h3>
            <p>Únete a nuestras actividades espirituales y comunitarias</p>
        </div>
        """, unsafe_allow_html=True)
        
        for evento in eventos[:2]:
            with st.container():
                st.markdown(f"""
                <div class="event-card">
                    <h4>{evento['nombre']}</h4>
                    <p><b>Fecha:</b> {evento['fecha'].strftime('%d/%m/%Y')}</p>
                    <p><b>Lugar:</b> {evento['lugar']}</p>
                    <p>{evento['descripcion']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="section">
            <h3>Ministerios Activos</h3>
            <p>Descubre cómo puedes servir en nuestra comunidad</p>
        </div>
        """, unsafe_allow_html=True)
        
        for ministerio in ministerios:
            with st.container():
                st.markdown(f"""
                <div class="event-card">
                    <h4>{ministerio['nombre']}</h4>
                    <p><b>Responsable:</b> {ministerio['responsable']}</p>
                    <p><b>Contacto:</b> {ministerio['contacto']}</p>
                </div>
                """, unsafe_allow_html=True)

# Página de Eventos
elif seccion == "📅 Eventos":
    st.markdown('<div class="section"><h2>Eventos y Actividades</h2></div>', unsafe_allow_html=True)
    
    # Mostrar todos los eventos
    for evento in eventos:
        with st.container():
            st.markdown(f"""
            <div class="event-card">
                <h3>{evento['nombre']}</h3>
                <p><b>Fecha:</b> {evento['fecha'].strftime('%A, %d de %B de %Y')}</p>
                <p><b>Lugar:</b> {evento['lugar']}</p>
                <p>{evento['descripcion']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón de registro
            if st.button("Registrarme", key=f"reg_{evento['id']}"):
                st.success(f"¡Te has registrado exitosamente para {evento['nombre']}!")
                st.balloons()

# Página de Donaciones
elif seccion == "💖 Donaciones":
    st.markdown('<div class="section"><h2>Apoya Nuestra Misión</h2></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="section">
        <p>Tu generosidad nos permite continuar con nuestra labor espiritual y comunitaria</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("formulario_donacion"):
        st.subheader("Información Personal")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
        with col2:
            email = st.text_input("Correo electrónico", placeholder="ejemplo@correo.com")
        
        st.subheader("Detalles de Donación")
        
        col1, col2 = st.columns(2)
        with col1:
            monto = st.number_input("Monto a donar", min_value=1.0, value=50.0, step=5.0)
        with col2:
            moneda = st.selectbox("Moneda", ["USD", "EUR", "MXN", "CLP", "COP"])
        
        frecuencia = st.radio("Frecuencia", ["Una vez", "Mensual", "Trimestral", "Anual"])
        proposito = st.selectbox("Destinar a", 
                                ["- Seleccionar -", "Misiones Internacionales", "Ayuda Comunitaria", "Mantenimiento de Instalaciones"])
        
        st.subheader("Método de Pago")
        metodo_pago = st.selectbox("Método de pago", ["Tarjeta de Crédito/Débito", "Transferencia Bancaria", "PayPal"])
        
        acepto = st.checkbox("Acepto que mi donación sea usada según los propósitos de la organización")
        
        submitted = st.form_submit_button("Realizar Donación")
        
        if submitted:
            if not nombre or not email:
                st.error("Por favor completa los campos obligatorios (Nombre y Email)")
            elif not acepto:
                st.error("Debes aceptar los términos de uso de la donación")
            else:
                st.success("¡Donación realizada con éxito! Gracias por tu generosidad.")
                st.balloons()
                st.markdown(f"""
                **Resumen de tu donación:**
                - Monto: {monto} {moneda}
                - Frecuencia: {frecuencia}
                - Propósito: {proposito if proposito != "- Seleccionar -" else "General"}
                """)

# Página de Directorio
elif seccion == "👥 Directorio":
    st.markdown('<div class="section"><h2>Directorio de Contactos</h2></div>', unsafe_allow_html=True)
    
    # Buscador
    busqueda = st.text_input("Buscar por nombre o ministerio")
    
    # Mostrar personal
    for persona in personal:
        if not busqueda or busqueda.lower() in persona['nombre'].lower() or busqueda.lower() in persona['cargo'].lower():
            with st.container():
                st.markdown(f"""
                <div class="contact-card">
                    <img src="https://ui-avatars.com/api/?name={persona['nombre'].replace(' ', '+')}&background=4b6cb7&color=fff" width="60">
                    <div>
                        <h4>{persona['nombre']}</h4>
                        <p><b>{persona['cargo']}</b></p>
                        <p>✉️ {persona['contacto']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Página de Contacto
elif seccion == "📞 Contacto":
    st.markdown('<div class="section"><h2>Contáctanos</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Información de Contacto")
        st.markdown("""
        **Dirección:**  
        Calle Principal #123  
        Ciudad, País  
        
        **Teléfono:**  
        +1 (123) 456-7890  
        
        **Correo Electrónico:**  
        info@comunidad.org  
        
        **Horario de Oficina:**  
        Lunes a Viernes: 9:00 AM - 5:00 PM  
        Sábados: 9:00 AM - 1:00 PM  
        """)
        
        st.subheader("Ministerios")
        for ministerio in ministerios:
            st.markdown(f"""
            **{ministerio['nombre']}**  
            {ministerio['responsable']}  
            ✉️ {ministerio['contacto']}
            """)
    
    with col2:
        st.subheader("Envíanos un Mensaje")
        with st.form("formulario_contacto"):
            nombre = st.text_input("Nombre", placeholder="Tu nombre completo")
            email = st.text_input("Correo Electrónico", placeholder="tu@correo.com")
            asunto = st.selectbox("Asunto", 
                                 ["- Seleccionar -", 
                                  "Información sobre eventos", 
                                  "Consulta espiritual", 
                                  "Donaciones", 
                                  "Voluntariado"])
            mensaje = st.text_area("Mensaje", height=150, placeholder="Escribe tu mensaje aquí...")
            
            submitted = st.form_submit_button("Enviar Mensaje")
            if submitted:
                if not nombre or not email or not mensaje or asunto == "- Seleccionar -":
                    st.error("Por favor completa todos los campos obligatorios")
                else:
                    st.success("¡Mensaje enviado con éxito! Te responderemos a la brevedad.")

# Footer
st.markdown("""
<hr style="margin-top: 30px;">
<div style="text-align: center; padding: 20px; color: #666;">
    <p>Comunidad de Fe &copy; 2023 - Todos los derechos reservados</p>
    <p>Síguenos en nuestras redes sociales: [Facebook] [Instagram] [YouTube]</p>
</div>
""", unsafe_allow_html=True)