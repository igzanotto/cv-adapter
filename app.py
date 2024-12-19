import streamlit as st
import warnings
import os
import asyncio
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai_tools import (
    FileReadTool,
    ScrapeWebsiteTool,
    MDXSearchTool,
    SerperDevTool
)

# Warning control
warnings.filterwarnings('ignore')

def setup_llm():
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.environ["GOOGLE_API_KEY"],
        temperature=0.7
    )

def create_agents_and_tasks(llm, resume_content):
    # Save resume content to a temporary file with explicit encoding
    with open('temp_resume.md', 'w', encoding='utf-8') as f:
        f.write(resume_content)

    # Initialize tools
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool()
    read_resume = FileReadTool(file_path='./temp_resume.md')
    semantic_search_resume = MDXSearchTool(mdx='./temp_resume.md')

    researcher = Agent(
        role="Tech Job Researcher",
        goal="Make sure to do amazing analysis on job posting to help job applicants",
        tools=[scrape_tool, search_tool],
        verbose=True,
        llm=llm,
        backstory="As a Job Researcher, your prowess in navigating and extracting critical information from job postings is unmatched."
    )

    research_task = Task(
        description=(
            "Analyze the job posting URL provided ({job_posting_url}) "
            "to extract key skills, experiences, and qualifications required."
        ),
        expected_output="A structured list of job requirements.",
        agent=researcher,
        async_execution=False
    )

    return [researcher], [research_task]

async def process_application(job_posting_url, github_url, personal_writeup, resume_content):
    llm = setup_llm()
    agents, tasks = create_agents_and_tasks(llm, resume_content)
    
    job_application_crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True
    )

    job_application_inputs = {
        'job_posting_url': job_posting_url,
        'github_url': github_url,
        'personal_writeup': personal_writeup
    }

    result = job_application_crew.kickoff(inputs=job_application_inputs)
    return result

def main():
    st.title("Job Application Assistant")
    st.write("Let us help you tailor your job application materials!")

    job_posting_url = st.text_input("Job Posting URL", 
        placeholder="Enter the job posting URL...")
    
    github_url = st.text_input("GitHub Profile URL", 
        placeholder="Enter your GitHub profile URL...")
    
    personal_writeup = st.text_area("Personal Write-up", 
        placeholder="Enter a brief description about yourself...")
    
    resume_content = st.text_area("Your Resume (in Markdown format)", 
        placeholder="Paste your resume in markdown format...")

    if st.button("Generate Application Materials"):
        if job_posting_url and github_url and personal_writeup and resume_content:
            with st.spinner("Processing your application materials..."):
                try:
                    # Create new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the async function
                    result = loop.run_until_complete(
                        process_application(job_posting_url, github_url, personal_writeup, resume_content)
                    )
                    
                    # Close the loop
                    loop.close()

                    st.success("Application materials generated successfully!")
                    st.write("Results:", result)
                    
                    # Display generated materials if they exist with proper encoding
                    if os.path.exists("tailored_resume.md"):
                        with open("tailored_resume.md", "r", encoding='utf-8') as f:
                            st.markdown("## Tailored Resume")
                            st.markdown(f.read())
                    
                    if os.path.exists("interview_materials.md"):
                        with open("interview_materials.md", "r", encoding='utf-8') as f:
                            st.markdown("## Interview Materials")
                            st.markdown(f.read())

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please fill in all fields before proceeding.")

if __name__ == "__main__":
    main()