from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cosentyx-ocr-extractor",
    version="1.0.0",
    author="Cosentyx Team",
    description="OCR Solution for Cosentyx/EMA Start Form Data Extraction using AWS Textract and Bedrock",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hsavaliya702/cosentyx-ocr-extractor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.34.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "Pillow>=10.1.0",
        "requests>=2.31.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "isort>=5.13.0",
        ],
    },
)
