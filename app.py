"""
# =====================
# Author: Chaitanya
# Project: CareerCraft Resume AI
# =====================
Smart Resume Analyzer using AI - Main Application
"""
import streamlit as st

# Set page config at the very beginning
st.set_page_config(
    page_title="Smart Resume Analyzer using AI",
    page_icon="🚀",
    layout="wide"
)

import os
import pandas as pd
import traceback
from utils.resume_analyzer import ResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data, 
    init_database, verify_admin, log_admin_action
)
from config.job_roles import JOB_ROLES
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from dashboard.dashboard import DashboardManager
import requests
from streamlit_lottie import st_lottie
import base64
import io
from datetime import datetime

class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }
        
        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
            
        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False
        
        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME Assistant": self.render_analyzer,
            "📝 RESUME BUDDY": self.render_builder,
            "📊 DASHBOARD": self.render_dashboard,
            "ℹ️ ABOUT": self.render_about
        }
        
        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()
        
        self.analyzer = ResumeAnalyzer()
        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES
        
        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None
        
        # Initialize database
        init_database()
        
        # Load external CSS
        with open('ui/global_style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        
        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()


    def export_to_excel(self):
        """Export resume data to Excel"""
        conn = get_database_connection()
        
        # Get resume data with analysis
        query = """
            SELECT 
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        
        try:
            # Read data into DataFrame
            df = pd.read_sql_query(query, conn)
            
            # Create Excel writer object
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')
            
            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()

    def render_dashboard(self):
        """Render the dashboard page"""
        self.dashboard_manager.render_dashboard()

    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def render_builder(self):
        st.title("Resume Buddy 📝")
        st.write("Build your dream resume quickly and easily with Resume Buddy!")
        
        # Template selection
        template_options = ["Modern", "Professional", "Minimal", "Creative"]
        selected_template = st.selectbox("Select Resume Template", template_options)
        st.success(f"🎨 Currently using: {selected_template} Template")

        # Personal Information
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            # Get existing values from session state
            existing_name = st.session_state.form_data['personal_info']['full_name']
            existing_email = st.session_state.form_data['personal_info']['email']
            existing_phone = st.session_state.form_data['personal_info']['phone']
            
            # Input fields with existing values
            full_name = st.text_input("Full Name", value=existing_name)
            email = st.text_input("Email", value=existing_email, key="email_input")
            phone = st.text_input("Phone", value=existing_phone)

            # Immediately update session state after email input
            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input
        
        with col2:
            # Get existing values from session state
            existing_location = st.session_state.form_data['personal_info']['location']
            existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
            existing_portfolio = st.session_state.form_data['personal_info']['portfolio']
            
            # Input fields with existing values
            location = st.text_input("Location", value=existing_location)
            linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
            portfolio = st.text_input("Portfolio Website", value=existing_portfolio)

        # Update personal info in session state
        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        # Professional Summary
        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             help="Write a brief summary highlighting your key skills and experience")
        
        # Experience Section
        st.subheader("Work Experience")
        if 'experiences' not in st.session_state.form_data:
            st.session_state.form_data['experiences'] = []
            
        if st.button("Add Experience"):
            st.session_state.form_data['experiences'].append({
                'company': '',
                'position': '',
                'start_date': '',
                'end_date': '',
                'description': '',
                'responsibilities': [],
                'achievements': []
            })
        
        for idx, exp in enumerate(st.session_state.form_data['experiences']):
            with st.expander(f"Experience {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    exp['company'] = st.text_input("Company Name", key=f"company_{idx}", value=exp.get('company', ''))
                    exp['position'] = st.text_input("Position", key=f"position_{idx}", value=exp.get('position', ''))
                with col2:
                    exp['start_date'] = st.text_input("Start Date", key=f"start_date_{idx}", value=exp.get('start_date', ''))
                    exp['end_date'] = st.text_input("End Date", key=f"end_date_{idx}", value=exp.get('end_date', ''))
                
                exp['description'] = st.text_area("Role Overview", key=f"desc_{idx}", 
                                                value=exp.get('description', ''),
                                                help="Brief overview of your role and impact")
                
                # Responsibilities
                st.markdown("##### Key Responsibilities")
                resp_text = st.text_area("Enter responsibilities (one per line)", 
                                       key=f"resp_{idx}",
                                       value='\n'.join(exp.get('responsibilities', [])),
                                       height=100,
                                       help="List your main responsibilities, one per line")
                exp['responsibilities'] = [r.strip() for r in resp_text.split('\n') if r.strip()]
                
                # Achievements
                st.markdown("##### Key Achievements")
                achv_text = st.text_area("Enter achievements (one per line)", 
                                       key=f"achv_{idx}",
                                       value='\n'.join(exp.get('achievements', [])),
                                       height=100,
                                       help="List your notable achievements, one per line")
                exp['achievements'] = [a.strip() for a in achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                    st.session_state.form_data['experiences'].pop(idx)
                    st.rerun()
        
        # Projects Section
        st.subheader("Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []
            
        if st.button("Add Project"):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })
        
        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"Project {idx + 1}", expanded=True):
                proj['name'] = st.text_input("Project Name", key=f"proj_name_{idx}", value=proj.get('name', ''))
                proj['technologies'] = st.text_input("Technologies Used", key=f"proj_tech_{idx}", 
                                                   value=proj.get('technologies', ''),
                                                   help="List the main technologies, frameworks, and tools used")
                
                proj['description'] = st.text_area("Project Overview", key=f"proj_desc_{idx}", 
                                                 value=proj.get('description', ''),
                                                 help="Brief overview of the project and its goals")
                
                # Project Responsibilities
                st.markdown("##### Key Responsibilities")
                proj_resp_text = st.text_area("Enter responsibilities (one per line)", 
                                            key=f"proj_resp_{idx}",
                                            value='\n'.join(proj.get('responsibilities', [])),
                                            height=100,
                                            help="List your main responsibilities in the project")
                proj['responsibilities'] = [r.strip() for r in proj_resp_text.split('\n') if r.strip()]
                
                # Project Achievements
                st.markdown("##### Key Achievements")
                proj_achv_text = st.text_area("Enter achievements (one per line)", 
                                            key=f"proj_achv_{idx}",
                                            value='\n'.join(proj.get('achievements', [])),
                                            height=100,
                                            help="List the project's key achievements and your contributions")
                proj['achievements'] = [a.strip() for a in proj_achv_text.split('\n') if a.strip()]
                
                proj['link'] = st.text_input("Project Link (optional)", key=f"proj_link_{idx}", 
                                           value=proj.get('link', ''),
                                           help="Link to the project repository, demo, or documentation")
                
                if st.button("Remove Project", key=f"remove_proj_{idx}"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()
        
        # Education Section
        st.subheader("Education")
        if 'education' not in st.session_state.form_data:
            st.session_state.form_data['education'] = []
            
        if st.button("Add Education"):
            st.session_state.form_data['education'].append({
                'school': '',
                'degree': '',
                'field': '',
                'graduation_date': '',
                'gpa': '',
                'achievements': []
            })
        
        for idx, edu in enumerate(st.session_state.form_data['education']):
            with st.expander(f"Education {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['school'] = st.text_input("School/University", key=f"school_{idx}", value=edu.get('school', ''))
                    edu['degree'] = st.text_input("Degree", key=f"degree_{idx}", value=edu.get('degree', ''))
                with col2:
                    edu['field'] = st.text_input("Field of Study", key=f"field_{idx}", value=edu.get('field', ''))
                    edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}", 
                                                         value=edu.get('graduation_date', ''))
                
                edu['gpa'] = st.text_input("GPA (optional)", key=f"gpa_{idx}", value=edu.get('gpa', ''))
                
                # Educational Achievements
                st.markdown("##### Achievements & Activities")
                edu_achv_text = st.text_area("Enter achievements (one per line)", 
                                           key=f"edu_achv_{idx}",
                                           value='\n'.join(edu.get('achievements', [])),
                                           height=100,
                                           help="List academic achievements, relevant coursework, or activities")
                edu['achievements'] = [a.strip() for a in edu_achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Education", key=f"remove_edu_{idx}"):
                    st.session_state.form_data['education'].pop(idx)
                    st.rerun()
        
        # Skills Section
        st.subheader("Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }
        
        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area("Technical Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['technical']),
                                     height=150,
                                     help="Programming languages, frameworks, databases, etc.")
            st.session_state.form_data['skills_categories']['technical'] = [s.strip() for s in tech_skills.split('\n') if s.strip()]
            
            soft_skills = st.text_area("Soft Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['soft']),
                                     height=150,
                                     help="Leadership, communication, problem-solving, etc.")
            st.session_state.form_data['skills_categories']['soft'] = [s.strip() for s in soft_skills.split('\n') if s.strip()]
        
        with col2:
            languages = st.text_area("Languages (one per line)", 
                                   value='\n'.join(st.session_state.form_data['skills_categories']['languages']),
                                   height=150,
                                   help="Programming or human languages with proficiency level")
            st.session_state.form_data['skills_categories']['languages'] = [l.strip() for l in languages.split('\n') if l.strip()]
            
            tools = st.text_area("Tools & Technologies (one per line)", 
                               value='\n'.join(st.session_state.form_data['skills_categories']['tools']),
                               height=150,
                               help="Development tools, software, platforms, etc.")
            st.session_state.form_data['skills_categories']['tools'] = [t.strip() for t in tools.split('\n') if t.strip()]
        
        # Update form data in session state
        st.session_state.form_data.update({
            'summary': summary
        })
        
        # Generate Resume button
        if st.button("Generate Resume 📄", type="primary"):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(f"Email input value: {st.session_state.get('email_input', '')}")
            
            # Get the current values from form
            current_name = st.session_state.form_data['personal_info']['full_name'].strip()
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''
            
            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")
            
            # Validate required fields
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return
            
            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return
                
            # Update email in form data one final time
            st.session_state.form_data['personal_info']['email'] = current_email
            
            try:
                print("Preparing resume data...")
                # Prepare resume data with current form values
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }
                
                print(f"Resume data prepared: {resume_data}")
                
                try:
                    # Generate resume
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            # Save resume data to database
                            save_resume_data(resume_data)
                            
                            # Offer the resume for download
                            st.success("✅ Resume generated successfully!")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        except Exception as db_error:
                            print(f"Warning: Failed to save to database: {str(db_error)}")
                            # Still allow download even if database save fails
                            st.warning("⚠️ Resume generated but couldn't be saved to database")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    else:
                        st.error("❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")
                        
            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")
    
    def render_about(self):
        """Render the about page"""
        # Apply modern styles
        # Function to load image as base64
        def get_image_as_base64(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode()
                    return f"data:image/jpeg;base64,{encoded}"
            except:
                return None
        
        # Get image path and convert to base64
        image_path = os.path.join(os.path.dirname(__file__), "assets", "sample.jpg")
        image_base64 = get_image_as_base64(image_path)
        
        # Add Font Awesome icons and custom CSS
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <style>
                .profile-section, .vision-section, .feature-card {
                    text-align: center;
                    padding: 2rem;
                    background: rgba(45, 45, 45, 0.9);
                    border-radius: 20px;
                    margin: 2rem auto;
                    max-width: 800px;
                }
                
                .profile-image {
                    width: 200px;
                    height: 200px;
                    border-radius: 50%;
                    margin: 0 auto 1.5rem;
                    display: block;
                    object-fit: cover;
                    border: 4px solid #4CAF50;
                }
                
                .profile-name {
                    font-size: 2.5rem;
                    color: white;
                    margin-bottom: 0.5rem;
                }
                
                .profile-title {
                    font-size: 1.2rem;
                    color: #4CAF50;
                    margin-bottom: 1.5rem;
                }
                
                .social-links {
                    display: flex;
                    justify-content: center;
                    gap: 1.5rem;
                    margin: 2rem 0;
                }
                
                .social-link {
                    font-size: 2rem;
                    color: #4CAF50;
                    transition: all 0.3s ease;
                    padding: 0.5rem;
                    border-radius: 50%;
                    background: rgba(76, 175, 80, 0.1);
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                }
                
                .social-link:hover {
                    transform: translateY(-5px);
                    background: #4CAF50;
                    color: white;
                    box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
                }
                
                .bio-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    margin-top: 2rem;
                    text-align: left;
                }

                .vision-text {
                    color: #ddd;
                    line-height: 1.8;
                    font-size: 1.1rem;
                    font-style: italic;
                    margin: 1.5rem 0;
                    text-align: left;
                }

                .vision-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .vision-title {
                    font-size: 2rem;
                    color: white;
                    margin-bottom: 1rem;
                }

                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 2rem;
                    margin: 2rem auto;
                    max-width: 1200px;
                }

                .feature-card {
                    padding: 2rem;
                    margin: 0;
                }

                .feature-icon {
                    font-size: 2.5rem;
                    color: #4CAF50;
                    margin-bottom: 1rem;
                }

                .feature-title {
                    font-size: 1.5rem;
                    color: white;
                    margin: 1rem 0;
                }

                .feature-description {
                    color: #ddd;
                    line-height: 1.6;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Hero Section
        st.markdown("""
            <div class="hero-section">
                <h1 class="hero-title">About Smart Resume Analyzer using AI</h1>
                <p class="hero-subtitle">A smart, AI-powered platform designed to help you optimize your resume and unlock your career potential with personalized insights and recommendations.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Profile Section
        st.markdown(f"""
            <div class="profile-section">
                <img src="{image_base64 if image_base64 else 'https://avatars.githubusercontent.com/Hunterdii'}" 
                     alt="Chaitanya" 
                     class="profile-image"
                     onerror="this.onerror=null; this.src='https://avatars.githubusercontent.com/Hunterdii';">
                <h2 class="profile-name">Chaitanya  Pasam</h2>
                <p class="profile-title">Full Stack Developer & AI/ML Enthusiast</p>
                <div class="social-links">
                    <a href="https://github.com/chaitanyachaitu09/chaitanyachaitu09" class="social-link" target="_blank">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="https://www.linkedin.com/in/chaitanya-pasam-91bb59186/" class="social-link" target="_blank">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    <a href="mailto:pasamchaitanya98@gmail.com" class="social-link" target="_blank">
                        <i class="fas fa-envelope"></i>
                    </a>
                </div>
                <p class="bio-text">
                  Hi there! I'm Chaitanya, a passionate Full Stack Developer with a love for AI and Machine Learning. I created Smart Resume Analyzer to help job seekers take control of their career journeys by optimizing their resumes with cutting-edge AI. With a background in both software development and AI, my goal is to empower users with intelligent, data-driven insights that help them stand out in a competitive job market. I also specialize in building static websites with a focus on UI/UX design, using HTML, CSS, and a bit of React JS to create clean, responsive websites that are not only functional but also a pleasure to use.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Vision Section
        st.markdown("""
            <div class="vision-section">
                <i class="fas fa-lightbulb vision-icon"></i>
                <h2 class="vision-title">Our Mission and Vision</h2>
                <p class="vision-text">
                    "At Smart Resume Analyzer, our mission is to make career opportunities accessible to everyone — not just those with polished resumes, insider connections, or years of experience. We combine cutting-edge AI with thoughtful, intuitive design to empower job seekers at every stage to uncover their strengths, tell their stories authentically, and shine in today’s competitive world. Our vision is simple yet powerful: to democratize career advancement through technology, giving everyone a fair chance to succeed. Because your story deserves to be told — and we’re here to help you tell it right."
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Features Section
        st.markdown("""
            <div class="features-grid">
                <div class="feature-card">
                    <i class="fas fa-robot feature-icon"></i>
                    <h3 class="feature-title">AI-Powered Resume Boost</h3>
                    <p class="feature-description">
                        Our smart AI gives you thoughtful feedback and easy ways to make your resume stand out — so your next opportunity is closer than you think.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-chart-line feature-icon"></i>
                    <h3 class="feature-title">Next-Gen Career Insights</h3>
                    <p class="feature-description">
                        Get clear, practical recommendations powered by real data and industry trends — helping you make smarter choices and move your career forward with confidence.
                    </p>
                </div>
                <div class="feature-card">
                    <i class="fas fa-shield-alt feature-icon"></i>
                    <h3 class="feature-title">Privacy First</h3>
                    <p class="feature-description">
                        Your security matters to us. We’re committed to keeping your information safe and private, ensuring that your data is always protected.
                    </p>
                </div>
            </div>
            <div style="text-align: center; margin: 3rem 0;">
                <a href="?page=analyzer" class="cta-button">
                    Start Your Journey
                    <i class="fas fa-arrow-right" style="margin-left: 10px;"></i>
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    def render_analyzer(self):
        """Render the resume analyzer page"""
        
        # Page Header
        page_header(
            " Smart Resume Assistant " 
           
            "Receive instant feedback to fine-tune your resume and increase your chances of standing out."
        )
        
        # Job Role Selection
        categories = list(self.job_roles.keys())
        selected_category = st.selectbox("Job Category", categories)
        
        roles = list(self.job_roles[selected_category].keys())
        selected_role = st.selectbox("Choose Role", roles)
        
        role_info = self.job_roles[selected_category][selected_role]
        
        # Display role information
        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>{selected_role}</h3>
            <p>{role_info['description']}</p>
            <h4>Required Skills:</h4>
            <p>{', '.join(role_info['required_skills'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File Upload
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])
        
        st.markdown(
            self.render_empty_state(
            "fas fa-cloud-upload-alt",
            "Upload your resume to get started with AI-powered analysis"
            ),
            unsafe_allow_html=True
        )
        if uploaded_file:
            with st.spinner("Analyzing your document..."):
                # Get file content
                text = ""
                try:
                    if uploaded_file.type == "application/pdf":
                        text = self.analyzer.extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        text = self.analyzer.extract_text_from_docx(uploaded_file)
                    else:
                        text = uploaded_file.getvalue().decode()
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    return

                
                # Analyze the document
                analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                
                # Save resume data to database
                resume_data = {
                    'personal_info': {
                        'name': analysis.get('name', ''),
                        'email': analysis.get('email', ''),
                        'phone': analysis.get('phone', ''),
                        'linkedin': analysis.get('linkedin', ''),
                        'github': analysis.get('github', ''),
                        'portfolio': analysis.get('portfolio', '')
                    },
                    'summary': analysis.get('summary', ''),
                    'target_role': selected_role,
                    'target_category': selected_category,
                    'education': analysis.get('education', []),
                    'experience': analysis.get('experience', []),
                    'projects': analysis.get('projects', []),
                    'skills': analysis.get('skills', []),
                    'template': ''
                }
                
                # Save to database
                try:
                    resume_id = save_resume_data(resume_data)
                    
                    # Save analysis data
                    analysis_data = {
                        'resume_id': resume_id,
                        'ats_score': analysis['ats_score'],
                        'keyword_match_score': analysis['keyword_match']['score'],
                        'format_score': analysis['format_score'],
                        'section_score': analysis['section_score'],
                        'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                        'recommendations': ','.join(analysis['suggestions'])
                    }
                    save_analysis_data(resume_id, analysis_data)
                    st.success("Resume data saved successfully!")
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")
                    print(f"Database error: {e}")
                
                # Show results based on document type
                if analysis.get('document_type') != 'resume':
                    st.error(f"⚠️ This appears to be a {analysis['document_type']} document, not a resume!")
                    st.warning("Please upload a proper resume for ATS analysis.")
                    return                
                # Display results in a modern card layout
                col1, col2 = st.columns(2)
                
                with col1:
                    # ATS Score Card with circular progress
                    st.markdown("""
                    <div class="feature-card">
                        <h2>ATS Score</h2>
                        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                            <div style="
                                position: absolute;
                                width: 150px;
                                height: 150px;
                                border-radius: 50%;
                                background: conic-gradient(
                                    #4CAF50 0% {score}%,
                                    #2c2c2c {score}% 100%
                                );
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            ">
                                <div style="
                                    width: 120px;
                                    height: 120px;
                                    background: #1a1a1a;
                                    border-radius: 50%;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: {color};
                                ">
                                    {score}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 10px;">
                            <span style="
                                font-size: 1.2em;
                                color: {color};
                                font-weight: bold;
                            ">
                                {status}
                            </span>
                        </div>
                    """.format(
                        score=analysis['ats_score'],
                        color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis['ats_score'] >= 60 else '#FF4444',
                        status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis['ats_score'] >= 60 else 'Needs Improvement'
                    ), unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                                        
                    # self.display_analysis_results(analysis_results)

                    # Skills Match Card
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Skills Match</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")
                    
                    if analysis['keyword_match']['missing_skills']:
                        st.markdown("#### Missing Skills:")
                        for skill in analysis['keyword_match']['missing_skills']:
                            st.markdown(f"- {skill}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    # Format Score Card
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Format Analysis</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Format Score", f"{int(analysis.get('format_score', 0))}%")
                    st.metric("Section Score", f"{int(analysis.get('section_score', 0))}%")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Suggestions Card with improved UI
                    st.markdown("""
                    <div class="feature-card">
                        <h2>📋 Resume Improvement Suggestions</h2>
                    """, unsafe_allow_html=True)
                    
                    # Contact Section
                    if analysis.get('contact_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('contact_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Summary Section
                    if analysis.get('summary_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('summary_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Skills Section
                    if analysis.get('skills_suggestions') or analysis['keyword_match']['missing_skills']:
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('skills_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>", unsafe_allow_html=True)
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Experience Section
                    if analysis.get('experience_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('experience_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Education Section
                    if analysis.get('education_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎓 Education</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('education_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # General Formatting Suggestions
                    if analysis.get('format_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('format_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                

                
                # Course Recommendations
                st.markdown("""
                <div class="feature-card">
                    <h2>📚 Recommended Courses</h2>
                """, unsafe_allow_html=True)
                
                # Get courses based on role and category
                courses = get_courses_for_role(selected_role)
                if not courses:
                    category = get_category_for_role(selected_role)
                    courses = COURSES_BY_CATEGORY.get(category, {}).get(selected_role, [])
                
                # Display courses in a grid
                cols = st.columns(2)
                for i, course in enumerate(courses[:6]):  # Show top 6 courses
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h4>{course[0]}</h4>
                            <a href='{course[1]}' target='_blank'>View Course</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Learning Resources
                st.markdown("""
                <div class="feature-card">
                    <h2>📺 Helpful Videos</h2>
                """, unsafe_allow_html=True)
                
                tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])
                
                with tab1:
                    # Resume Videos
                    for category, videos in RESUME_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                with tab2:
                    # Interview Videos
                    for category, videos in INTERVIEW_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        # Close the page container
        st.markdown('</div>', unsafe_allow_html=True)

    def render_home(self):
        
        # Hero Section
        hero_section(
            "Smart Resume Analyzer using AI",
            "Transform and elevate your career with AI-driven resume analysis and smart building tools. Gain personalized insights and craft standout, professional resumes."
        )
        
        # Features Section
        st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
        
        feature_card(
            "fas fa-brain",
            "Advanced resume evaluation platform",
            "Optimize your resume with real-time analysis from advanced AI that pinpoints what works and what can be improved"
        )
        
        feature_card(
            "fas fa-chart-pie",
            "Get Career Insights",
            "Want to grow your career? Get smart tips and easy-to-understand insights just for you.."
        )

        feature_card(
            "fas fa-star",
            "Smart Resume Buddy",
            "Design professional resumes effortlessly with real-time tips on layout and what to include"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Call-to-Action with Streamlit navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Get Started", key="get_started_btn", 
                        help="Click to start analyzing your resume",
                        type="primary",
                        use_container_width=True):
                cleaned_name = "🔍 RESUME ANALYZER".lower().replace(" ", "_").replace("🔍", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()

    def main(self):
        
        # Admin login/logout in sidebar
        with st.sidebar:
            st_lottie(self.load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_jtbfg2nb.json"), height=200, key="sidebar_animation")
            st.title("Smart Resume Analyzer using AI")
            st.markdown("---")
            
            # Navigation buttons
            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()

            # Add some space before admin login
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Admin Login/Logout section at bottom
            if st.session_state.get('is_admin', False):
                st.success(f"Logged in as: {st.session_state.get('current_admin_email')}")
                if st.button("Logout", key="logout_button"):
                    try:
                        log_admin_action(st.session_state.get('current_admin_email'), "logout")
                        st.session_state.is_admin = False
                        st.session_state.current_admin_email = None
                        st.success("Logged out successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during logout: {str(e)}")
            else:
                with st.expander("👤 Admin Login"):
                    admin_email_input = st.text_input("Email", key="admin_email_input")
                    admin_password = st.text_input("Password", type="password", key="admin_password_input")
                    if st.button("Login", key="login_button"):
                            try:
                                if verify_admin(admin_email_input, admin_password):
                                    st.session_state.is_admin = True
                                    st.session_state.current_admin_email = admin_email_input
                                    log_admin_action(admin_email_input, "login")
                                    st.success("Logged in successfully!")
                                    st.rerun()
                                else:
                                    st.error("Invalid credentials")
                            except Exception as e:
                                st.error(f"Error during login: {str(e)}")
        
        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        # Get current page and render it
        current_page = st.session_state.get('page', 'home')
        
        # Create a mapping of cleaned page names to original names
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").replace("📊", "").replace("🎯", "").replace("💬", "").replace("ℹ️", "").strip(): name 
                       for name in self.pages.keys()}
        
        # Render the appropriate page
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            # Default to home page if invalid page
            self.render_home()
    
def page_header(title, subtitle=None):
    """Render a consistent page header with gradient background"""
    st.markdown(
        f'''
        <div class="page-header">
            <h1 class="header-title">{title}</h1>
            {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        ''',
        unsafe_allow_html=True
    )

def hero_section(title, subtitle=None, description=None):
    """Render a modern hero section with gradient background and animations"""
    # If description is provided but subtitle is not, use description as subtitle
    if description and not subtitle:
        subtitle = description
        description = None

    st.markdown(
        f'''
        <div class="page-header hero-header">
            <h1 class="header-title">{title}</h1>
            {f'<div class="header-subtitle">{subtitle}</div>' if subtitle else ''}
            {f'<p class="header-description">{description}</p>' if description else ''}
        </div>
        ''',
        unsafe_allow_html=True
    )

def feature_card(icon, title, description):
    """Render a modern feature card with hover effects"""
    st.markdown(f"""
        <div class="card feature-card">
            <div class="feature-icon icon-pulse">
                <i class="{icon}"></i>
            </div>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    app = ResumeApp()
    app.main()
