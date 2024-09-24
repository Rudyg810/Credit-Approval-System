# Credit Approval System

The Credit Approval System is a project developed using Python, Django, Postgres, and Docker, designed to streamline the credit evaluation process and facilitate banking-related operations. This project encompasses a robust backend system comprising multiple APIs for assessing credit scores, managing user data, and processing loan applications. Leveraging Docker, the entire project is containerized to ensure seamless deployment and version compatibility.

Within the system, various datasets stored in a Postgres database are utilized to analyze user data and determine eligibility for loans. Through intricate calculations, including assessment of risk factors and determination of interest rates based on tenure, the system provides accurate evaluations of loan applications. Whether it's fetching user data, creating new user profiles, or conducting in-depth financial analyses, the Credit Approval System offers a reliable platform for efficient banking operations.

## Steps to Run the Project

### 1. Clone the Repository
Begin by cloning the project repository to your local machine.

```bash
git clone <repository-url>
cd Alemeno
cd api
docker-compose build
docker-compose up
docker-compose run web python manage.py migrate
