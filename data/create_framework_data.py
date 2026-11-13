#!/usr/bin/env python3
"""
Create Framework and Syllabus PDF files for the Curriculum Gap Analysis Pipeline.

This script generates:
  - 3 framework PDFs (Data Science, Web Development, Cloud & DevOps)
  - 3 sample syllabus PDFs corresponding to each framework domain

Each framework contains 15 competencies with detailed descriptions.
Each syllabus intentionally omits 5 competencies (IDs *-011 through *-015)
to serve as known gaps for evaluation.

Frameworks are curated from public/open-licensed sources:
  - NIST NICE Framework (Public Domain)
  - ESCO Classification (CC BY 4.0)
  - ACM CS2023 Curricula Guidelines
"""

import os
import pymupdf as fitz

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMEWORK_DIR = os.path.join(BASE_DIR, "frameworks")
SYLLABUS_DIR = os.path.join(BASE_DIR, "syllabi")

os.makedirs(FRAMEWORK_DIR, exist_ok=True)
os.makedirs(SYLLABUS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper: write a multi-page PDF from structured text blocks
# ---------------------------------------------------------------------------

def _insert_text_block(page, y, text, fontsize=11, fontname="helv", color=(0, 0, 0), indent=0):
    """Insert a text block and return the new y position."""
    tw = fitz.TextWriter(page.rect)
    x = 54 + indent
    max_width = page.rect.width - 108 - indent
    lines = []
    # Simple word-wrap
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            tl = fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize)
            if tl > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

    for line in lines:
        if y > page.rect.height - 60:
            return None, line, lines[lines.index(line):]  # signal new page needed
        if line == "":
            y += fontsize * 0.6
            continue
        page.insert_text((x, y), line, fontsize=fontsize, fontname=fontname, color=color)
        y += fontsize * 1.4
    return y, None, None


def create_pdf(filepath, sections):
    """
    Create a PDF from a list of sections.
    Each section is a dict: {text, fontsize, fontname, color, indent, spacing_before}
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    y = 60

    for section in sections:
        text = section["text"]
        fontsize = section.get("fontsize", 11)
        fontname = section.get("fontname", "helv")
        color = section.get("color", (0, 0, 0))
        indent = section.get("indent", 0)
        spacing = section.get("spacing_before", 0)
        y += spacing

        # Word-wrap and paginate
        paragraphs = text.split("\n")
        for para in paragraphs:
            if not para.strip():
                y += fontsize * 0.6
                if y > page.rect.height - 60:
                    page = doc.new_page(width=595, height=842)
                    y = 60
                continue
            words = para.split()
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                tl = fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize)
                max_w = 595 - 108 - indent
                if tl > max_w and current_line:
                    if y > page.rect.height - 60:
                        page = doc.new_page(width=595, height=842)
                        y = 60
                    page.insert_text((54 + indent, y), current_line,
                                     fontsize=fontsize, fontname=fontname, color=color)
                    y += fontsize * 1.4
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                if y > page.rect.height - 60:
                    page = doc.new_page(width=595, height=842)
                    y = 60
                page.insert_text((54 + indent, y), current_line,
                                 fontsize=fontsize, fontname=fontname, color=color)
                y += fontsize * 1.4

    page_count = doc.page_count
    doc.save(filepath)
    doc.close()
    print(f"  Created: {filepath} ({page_count} pages)")


# ============================================================================
# DATA SCIENCE FRAMEWORK
# ============================================================================

DS_COMPETENCIES = [
    {
        "id": "DS-001",
        "title": "Statistical Analysis and Hypothesis Testing",
        "description": (
            "This competency covers the theoretical foundations and practical application of "
            "statistical methods for analysing data, drawing inferences, and making data-driven "
            "decisions. Practitioners must be able to formulate null and alternative hypotheses, "
            "select appropriate parametric and non-parametric tests (t-test, chi-square, ANOVA, "
            "Mann-Whitney U), compute p-values, and interpret confidence intervals. Understanding "
            "Type I and Type II errors, effect sizes, and statistical power is essential."
        ),
        "skills": "Descriptive statistics, inferential statistics, hypothesis formulation, p-value interpretation, confidence intervals, effect size estimation, ANOVA, chi-square test, t-tests, non-parametric methods."
    },
    {
        "id": "DS-002",
        "title": "Machine Learning Algorithms (Supervised Learning)",
        "description": (
            "Covers the design, implementation, and evaluation of supervised machine learning models "
            "that learn input-output mappings from labelled training data. Practitioners should "
            "understand decision trees, random forests, support vector machines, k-nearest neighbours, "
            "and gradient boosting methods. They must be able to split data into training, validation, "
            "and test sets, apply cross-validation, tune hyperparameters, and evaluate models using "
            "metrics such as accuracy, precision, recall, F1-score, and AUC-ROC."
        ),
        "skills": "Decision trees, random forests, SVM, kNN, gradient boosting, cross-validation, hyperparameter tuning, precision/recall, AUC-ROC, model selection."
    },
    {
        "id": "DS-003",
        "title": "Data Preprocessing and Cleaning",
        "description": (
            "Addresses the essential steps of transforming raw, messy data into a clean, structured "
            "format suitable for analysis and modelling. This includes handling missing values through "
            "imputation or removal, detecting and treating outliers, encoding categorical variables "
            "(one-hot, label, target encoding), scaling and normalising numerical features, and "
            "resolving data type inconsistencies. Practitioners must also understand data quality "
            "assessment techniques and be able to document preprocessing pipelines for reproducibility."
        ),
        "skills": "Missing value imputation, outlier detection, feature scaling, normalisation, categorical encoding, data type conversion, pipeline construction, data quality assessment."
    },
    {
        "id": "DS-004",
        "title": "Data Visualization and Reporting",
        "description": (
            "Focuses on the ability to create clear, accurate, and insightful visual representations "
            "of data to communicate findings to both technical and non-technical stakeholders. "
            "Practitioners should be proficient in tools such as Matplotlib, Seaborn, and Plotly for "
            "creating histograms, scatter plots, box plots, heatmaps, and interactive dashboards. "
            "They must understand principles of visual encoding, colour theory for data, and how to "
            "design visualisations that avoid common pitfalls like misleading axes or chart junk."
        ),
        "skills": "Matplotlib, Seaborn, Plotly, chart selection, dashboard design, visual encoding principles, storytelling with data, report writing."
    },
    {
        "id": "DS-005",
        "title": "Database Management and SQL",
        "description": (
            "Covers the fundamentals of relational database management systems and the use of SQL "
            "for data retrieval, manipulation, and aggregation. Practitioners must write complex "
            "queries involving JOINs (inner, outer, cross), subqueries, window functions, common "
            "table expressions, and GROUP BY with HAVING clauses. They should also understand "
            "database normalisation, indexing strategies, transaction management, and basic database "
            "administration concepts necessary for working with production data stores."
        ),
        "skills": "SQL (SELECT, JOIN, GROUP BY, subqueries, window functions, CTEs), database normalisation, indexing, transaction management, PostgreSQL/MySQL."
    },
    {
        "id": "DS-006",
        "title": "Python Programming for Data Science",
        "description": (
            "Encompasses proficiency in using Python as the primary programming language for data "
            "science workflows. Practitioners should master core Python (data structures, control "
            "flow, functions, classes, error handling) and essential libraries including NumPy for "
            "numerical computing, Pandas for data manipulation, and scikit-learn for machine learning. "
            "They must be able to write clean, modular, well-documented code and use virtual "
            "environments, package management, and version control for reproducible analysis."
        ),
        "skills": "Python 3.x, NumPy, Pandas, scikit-learn, Jupyter notebooks, virtual environments, pip, code modularity, PEP 8 compliance."
    },
    {
        "id": "DS-007",
        "title": "Linear Algebra and Calculus for ML",
        "description": (
            "Covers the mathematical foundations underpinning machine learning algorithms. "
            "Practitioners need to understand vectors, matrices, matrix operations (multiplication, "
            "transposition, inversion), eigenvalues and eigenvectors, and singular value decomposition. "
            "In calculus, they must grasp derivatives, partial derivatives, gradients, the chain rule, "
            "and their application in gradient descent optimisation. These concepts are critical for "
            "understanding how ML algorithms learn from data and how to debug convergence issues."
        ),
        "skills": "Vectors, matrices, matrix operations, eigenvalues/eigenvectors, SVD, derivatives, partial derivatives, gradient descent, chain rule, optimisation."
    },
    {
        "id": "DS-008",
        "title": "Probability and Bayesian Methods",
        "description": (
            "Focuses on probability theory as the foundation for statistical reasoning and Bayesian "
            "inference in data science. Practitioners should understand probability axioms, conditional "
            "probability, Bayes' theorem, probability distributions (normal, binomial, Poisson, "
            "exponential), and concepts of prior, likelihood, and posterior. They should be able to "
            "apply Bayesian reasoning to classification (Naive Bayes), A/B testing, and parameter "
            "estimation, understanding the advantages of Bayesian approaches over frequentist methods."
        ),
        "skills": "Probability axioms, conditional probability, Bayes' theorem, probability distributions, prior/posterior, Naive Bayes, Bayesian estimation, conjugate priors."
    },
    {
        "id": "DS-009",
        "title": "Exploratory Data Analysis (EDA)",
        "description": (
            "Covers the systematic approach to investigating datasets before formal modelling to "
            "discover patterns, spot anomalies, test assumptions, and generate hypotheses. EDA "
            "combines statistical summaries (mean, median, variance, skewness, kurtosis) with "
            "visual techniques (distributions, correlations, pair plots) to understand data structure. "
            "Practitioners must be able to profile datasets, identify feature relationships, detect "
            "multicollinearity, and determine appropriate transformations or feature engineering steps."
        ),
        "skills": "Summary statistics, distribution analysis, correlation analysis, pair plots, data profiling, feature relationships, multicollinearity detection, hypothesis generation."
    },
    {
        "id": "DS-010",
        "title": "Regression Analysis (Linear and Logistic)",
        "description": (
            "Covers the theory and practice of regression models for predicting continuous outcomes "
            "(linear regression) and categorical outcomes (logistic regression). Practitioners must "
            "understand ordinary least squares, gradient descent for parameter estimation, assumptions "
            "of linear regression (linearity, normality, homoscedasticity), regularisation techniques "
            "(L1 Lasso, L2 Ridge, Elastic Net), and logistic regression's sigmoid function and "
            "maximum likelihood estimation. Model diagnostics including residual analysis and "
            "multicollinearity checks via VIF are essential skills."
        ),
        "skills": "Linear regression, logistic regression, OLS, gradient descent, regularisation (L1/L2), residual analysis, VIF, odds ratios, maximum likelihood estimation."
    },
    {
        "id": "DS-011",
        "title": "MLOps and Model Deployment Pipelines",
        "description": (
            "Addresses the practices and tools for operationalising machine learning models, moving "
            "them from experimental notebooks to production-grade services. This includes model "
            "versioning, experiment tracking (MLflow, Weights & Biases), containerised model serving "
            "(Docker, Kubernetes), building CI/CD pipelines for ML, automated retraining triggers, "
            "A/B testing in production, model monitoring for data drift and concept drift, and "
            "maintaining model registries. MLOps bridges the gap between data science and software "
            "engineering to ensure reliable, scalable model deployment."
        ),
        "skills": "MLflow, Docker, Kubernetes, CI/CD for ML, model versioning, experiment tracking, model monitoring, data drift detection, model registries, feature stores."
    },
    {
        "id": "DS-012",
        "title": "Big Data Technologies (Spark, Hadoop)",
        "description": (
            "Covers distributed computing frameworks for processing datasets that exceed the capacity "
            "of single-machine memory and storage. Practitioners must understand the Hadoop ecosystem "
            "(HDFS, MapReduce, YARN), Apache Spark (RDDs, DataFrames, Spark SQL, Spark MLlib), and "
            "how to design data pipelines that scale horizontally. This includes partitioning "
            "strategies, data serialisation formats (Parquet, Avro, ORC), cluster resource management, "
            "and performance tuning. Understanding when big data tools are appropriate versus "
            "traditional approaches is also critical."
        ),
        "skills": "Apache Spark, Hadoop, HDFS, MapReduce, Spark SQL, Spark MLlib, Parquet, data partitioning, cluster management, PySpark."
    },
    {
        "id": "DS-013",
        "title": "Deep Learning and Neural Networks",
        "description": (
            "Encompasses the theory and practical implementation of artificial neural networks and "
            "deep learning architectures. Practitioners should understand feedforward networks, "
            "backpropagation, activation functions (ReLU, sigmoid, softmax), convolutional neural "
            "networks (CNNs) for image tasks, recurrent neural networks (RNNs/LSTMs) for sequential "
            "data, and transformer architectures. They must be proficient in deep learning frameworks "
            "(TensorFlow, PyTorch), understand GPU computing, and be able to apply techniques such as "
            "dropout, batch normalisation, transfer learning, and learning rate scheduling."
        ),
        "skills": "Neural network architecture, backpropagation, CNNs, RNNs, LSTMs, transformers, TensorFlow, PyTorch, transfer learning, GPU computing, dropout, batch normalisation."
    },
    {
        "id": "DS-014",
        "title": "Natural Language Processing (NLP)",
        "description": (
            "Covers computational techniques for analysing, understanding, and generating human "
            "language. Practitioners should understand text preprocessing (tokenisation, stemming, "
            "lemmatisation, stop-word removal), text representation (bag-of-words, TF-IDF, word "
            "embeddings like Word2Vec and GloVe), and modern approaches using transformer-based "
            "models (BERT, GPT). Key tasks include sentiment analysis, named entity recognition, "
            "text classification, topic modelling, machine translation, and question answering. "
            "Understanding evaluation metrics like BLEU, ROUGE, and perplexity is also necessary."
        ),
        "skills": "Tokenisation, TF-IDF, Word2Vec, GloVe, BERT, GPT, sentiment analysis, NER, text classification, topic modelling, spaCy, Hugging Face Transformers."
    },
    {
        "id": "DS-015",
        "title": "Data Ethics, Bias Detection and Responsible AI",
        "description": (
            "Addresses the ethical considerations and societal implications of data science and AI "
            "systems. Practitioners must understand sources of algorithmic bias (sampling bias, "
            "measurement bias, historical bias), fairness metrics (demographic parity, equalised "
            "odds, calibration), and bias mitigation techniques (pre-processing, in-processing, "
            "post-processing). They should be familiar with privacy regulations (GDPR, CCPA), "
            "differential privacy, model explainability (SHAP, LIME), and frameworks for responsible "
            "AI development including impact assessments and stakeholder engagement."
        ),
        "skills": "Fairness metrics, bias detection, SHAP, LIME, differential privacy, GDPR compliance, ethical frameworks, model explainability, AI impact assessment, responsible AI guidelines."
    },
]

# ============================================================================
# WEB DEVELOPMENT FRAMEWORK
# ============================================================================

WD_COMPETENCIES = [
    {
        "id": "WD-001",
        "title": "HTML5 Semantic Markup",
        "description": (
            "Covers the use of HTML5 semantic elements to create well-structured, meaningful web "
            "documents that convey content hierarchy and purpose to browsers, screen readers, and "
            "search engines. Practitioners must understand and correctly apply elements such as "
            "<header>, <nav>, <main>, <article>, <section>, <aside>, and <footer>. They should be "
            "able to create accessible forms with proper labelling, use ARIA roles when semantic "
            "elements are insufficient, and validate HTML for standards compliance."
        ),
        "skills": "Semantic HTML5 elements, document structure, forms and validation, ARIA roles, meta tags, SEO best practices, HTML validation."
    },
    {
        "id": "WD-002",
        "title": "CSS3 and Responsive Design",
        "description": (
            "Encompasses the ability to style web content using CSS3 and create layouts that adapt "
            "seamlessly to different screen sizes and devices. Practitioners should master the box "
            "model, Flexbox, CSS Grid, media queries, and relative units (em, rem, vw, vh). They "
            "must understand CSS specificity, the cascade, inheritance, and be proficient with "
            "preprocessors like SASS or PostCSS. Creating mobile-first designs and understanding "
            "responsive images and typography are essential skills for modern web development."
        ),
        "skills": "CSS3 selectors, Flexbox, CSS Grid, media queries, mobile-first design, SASS/SCSS, CSS variables, responsive images, animations, transitions."
    },
    {
        "id": "WD-003",
        "title": "JavaScript ES6+ Programming",
        "description": (
            "Covers proficiency in modern JavaScript (ES6 and beyond) as the core programming "
            "language for web development. Practitioners must understand let/const, arrow functions, "
            "template literals, destructuring, spread/rest operators, Promises, async/await, modules "
            "(import/export), classes, iterators, generators, and the Map/Set data structures. They "
            "should write clean, maintainable code using modern patterns and understand the event "
            "loop, closures, prototypal inheritance, and JavaScript's asynchronous programming model."
        ),
        "skills": "ES6+ syntax, Promises, async/await, modules, classes, closures, event loop, error handling, Array methods, functional programming patterns."
    },
    {
        "id": "WD-004",
        "title": "React Component Architecture",
        "description": (
            "Focuses on building user interfaces using React's component-based architecture. "
            "Practitioners should understand functional components, hooks (useState, useEffect, "
            "useContext, useReducer, useMemo, useCallback), component composition, props and state "
            "management, conditional rendering, and list rendering with keys. They must be able to "
            "manage application state using Context API or state management libraries (Redux, Zustand), "
            "implement client-side routing with React Router, and optimise rendering performance."
        ),
        "skills": "React components, hooks, state management, props, Context API, Redux, React Router, JSX, component lifecycle, performance optimisation."
    },
    {
        "id": "WD-005",
        "title": "RESTful API Design",
        "description": (
            "Covers the principles and best practices for designing and implementing RESTful APIs "
            "that enable communication between client and server applications. Practitioners must "
            "understand HTTP methods (GET, POST, PUT, PATCH, DELETE), status codes, resource naming "
            "conventions, URL structure, request/response headers, content negotiation, and HATEOAS. "
            "They should be able to design APIs that are consistent, well-documented (OpenAPI/Swagger), "
            "versioned, and handle pagination, filtering, sorting, and error responses properly."
        ),
        "skills": "HTTP methods, status codes, REST principles, API versioning, OpenAPI/Swagger, pagination, error handling, CORS, rate limiting, API documentation."
    },
    {
        "id": "WD-006",
        "title": "Version Control with Git",
        "description": (
            "Encompasses the use of Git for source code management and collaborative development "
            "workflows. Practitioners must understand core Git concepts (commits, branches, merges, "
            "rebases), be able to resolve merge conflicts, use feature branching strategies (Git Flow, "
            "GitHub Flow), create and review pull requests, write meaningful commit messages, and use "
            "tools like .gitignore, git stash, git cherry-pick, and interactive rebase. They should "
            "also understand Git hooks and integration with CI/CD pipelines."
        ),
        "skills": "Git commands, branching strategies, merge conflict resolution, pull requests, code review, Git Flow, commit conventions, .gitignore, GitHub/GitLab."
    },
    {
        "id": "WD-007",
        "title": "Relational Databases and SQL",
        "description": (
            "Covers the design and interaction with relational databases in the context of web "
            "applications. Practitioners should understand entity-relationship modelling, database "
            "normalisation (1NF through 3NF), writing efficient SQL queries, using ORMs (Sequelize, "
            "Prisma, TypeORM), database migrations, connection pooling, and query optimisation through "
            "indexing and query plans. They must also understand transactions, ACID properties, and "
            "how to design schemas that support web application requirements for performance and data "
            "integrity."
        ),
        "skills": "SQL, database design, normalisation, ORMs, migrations, indexing, query optimisation, transactions, ACID properties, PostgreSQL/MySQL."
    },
    {
        "id": "WD-008",
        "title": "Node.js Server-Side Development",
        "description": (
            "Focuses on building server-side applications using Node.js and its ecosystem. "
            "Practitioners should understand the Node.js event-driven, non-blocking I/O model, "
            "be able to build HTTP servers and RESTful APIs using Express.js or Fastify, implement "
            "middleware patterns, handle file I/O, manage environment variables, and work with npm "
            "packages. They must also understand error handling in asynchronous Node.js code, "
            "streaming, worker threads, and how to structure scalable Node.js applications."
        ),
        "skills": "Node.js, Express.js, middleware, npm, REST API development, environment variables, error handling, file I/O, streams, application structure."
    },
    {
        "id": "WD-009",
        "title": "Authentication and Authorization",
        "description": (
            "Covers the implementation of user identity verification (authentication) and access "
            "control (authorization) in web applications. Practitioners must understand session-based "
            "authentication, token-based authentication (JWT), OAuth 2.0, OpenID Connect, password "
            "hashing (bcrypt, argon2), multi-factor authentication, role-based access control (RBAC), "
            "and secure cookie management. They should be able to implement login/registration flows, "
            "protect routes, and understand common security vulnerabilities (XSS, CSRF, session "
            "hijacking) and their mitigations."
        ),
        "skills": "JWT, OAuth 2.0, session management, password hashing, RBAC, secure cookies, CSRF protection, XSS prevention, Passport.js, Auth0."
    },
    {
        "id": "WD-010",
        "title": "DOM Manipulation and Browser APIs",
        "description": (
            "Encompasses the ability to interact with and manipulate the Document Object Model (DOM) "
            "and leverage modern browser APIs. Practitioners should understand DOM traversal and "
            "manipulation methods, event handling and delegation, the browser rendering pipeline, and "
            "APIs such as Fetch, localStorage/sessionStorage, Intersection Observer, Web Workers, "
            "Geolocation, and the History API. They must be able to create dynamic, interactive web "
            "pages and understand performance implications of DOM operations and how to minimise "
            "layout thrashing."
        ),
        "skills": "DOM methods, event handling, event delegation, Fetch API, localStorage, Intersection Observer, Web Workers, History API, browser rendering, performance."
    },
    {
        "id": "WD-011",
        "title": "Web Accessibility (WCAG Standards)",
        "description": (
            "Covers the principles, guidelines, and techniques for making web content accessible to "
            "people with disabilities, following the Web Content Accessibility Guidelines (WCAG) 2.1. "
            "Practitioners must understand the four principles of accessibility (Perceivable, "
            "Operable, Understandable, Robust), implement proper focus management, keyboard "
            "navigation, screen reader compatibility, colour contrast requirements, and alternative "
            "text for media. They should be able to audit websites using accessibility testing tools "
            "(axe, Lighthouse, WAVE) and remediate common accessibility failures."
        ),
        "skills": "WCAG 2.1, ARIA attributes, keyboard navigation, screen reader testing, colour contrast, focus management, accessibility auditing, axe, Lighthouse, inclusive design."
    },
    {
        "id": "WD-012",
        "title": "Progressive Web Apps (PWA)",
        "description": (
            "Focuses on building web applications that provide native app-like experiences using "
            "modern web technologies. Practitioners should understand Service Workers for offline "
            "functionality and background sync, the Web App Manifest for installability, caching "
            "strategies (cache-first, network-first, stale-while-revalidate), push notifications "
            "via the Push API, and IndexedDB for client-side storage. They must be able to create "
            "reliable, fast, and engaging applications that work across devices and network conditions "
            "and pass PWA audits."
        ),
        "skills": "Service Workers, Web App Manifest, caching strategies, push notifications, IndexedDB, offline-first design, Workbox, installability, PWA audits."
    },
    {
        "id": "WD-013",
        "title": "GraphQL API Development",
        "description": (
            "Covers the design and implementation of GraphQL APIs as an alternative to REST for "
            "client-server data exchange. Practitioners must understand the GraphQL schema definition "
            "language (SDL), type system, queries, mutations, subscriptions, resolvers, and data "
            "loaders for batching. They should be able to build GraphQL servers using libraries like "
            "Apollo Server or Yoga, implement authentication and authorization in resolvers, handle "
            "N+1 query problems, design efficient schemas, and understand when GraphQL is preferable "
            "to REST."
        ),
        "skills": "GraphQL SDL, queries, mutations, subscriptions, resolvers, Apollo Server, data loaders, schema design, federation, GraphQL vs REST trade-offs."
    },
    {
        "id": "WD-014",
        "title": "Containerization and Docker for Web Apps",
        "description": (
            "Addresses the use of containerisation technology, primarily Docker, to package, deploy, "
            "and manage web applications and their dependencies consistently across environments. "
            "Practitioners must understand Docker images, Dockerfiles, multi-stage builds, Docker "
            "Compose for multi-container applications, volume management, networking between "
            "containers, environment variable injection, and image optimisation. They should be able "
            "to containerise both frontend and backend applications and integrate Docker into CI/CD "
            "workflows."
        ),
        "skills": "Docker, Dockerfiles, Docker Compose, multi-stage builds, container networking, volumes, image optimisation, container registries, Docker in CI/CD."
    },
    {
        "id": "WD-015",
        "title": "Web Performance Optimization and Core Web Vitals",
        "description": (
            "Covers techniques and metrics for optimising the loading speed, interactivity, and "
            "visual stability of web applications. Practitioners must understand Core Web Vitals "
            "(Largest Contentful Paint, First Input Delay / Interaction to Next Paint, Cumulative "
            "Layout Shift), code splitting, lazy loading, tree shaking, image optimisation (WebP, "
            "AVIF, responsive images), CDN configuration, HTTP caching headers, resource hints "
            "(preload, prefetch, preconnect), and critical rendering path optimisation. They should "
            "use performance profiling tools (Lighthouse, WebPageTest, Chrome DevTools Performance "
            "panel) to identify and resolve bottlenecks."
        ),
        "skills": "Core Web Vitals (LCP, FID/INP, CLS), code splitting, lazy loading, tree shaking, image optimisation, CDN, caching headers, Lighthouse, WebPageTest, critical rendering path."
    },
]

# ============================================================================
# CLOUD AND DEVOPS FRAMEWORK
# ============================================================================

CD_COMPETENCIES = [
    {
        "id": "CD-001",
        "title": "Linux System Administration",
        "description": (
            "Covers the foundational skills for managing Linux-based systems that underpin most "
            "cloud and DevOps environments. Practitioners must be proficient in navigating the "
            "filesystem, managing users and groups, configuring file permissions (chmod, chown), "
            "managing packages (apt, yum, dnf), working with systemd services, monitoring system "
            "resources (top, htop, vmstat, iostat), configuring network interfaces, and understanding "
            "the boot process. They should be able to troubleshoot common system issues, manage "
            "cron jobs, and secure Linux servers following hardening best practices."
        ),
        "skills": "Linux CLI, filesystem management, user/group management, permissions, package management, systemd, process management, cron, system monitoring, server hardening."
    },
    {
        "id": "CD-002",
        "title": "Cloud Computing Fundamentals (IaaS, PaaS, SaaS)",
        "description": (
            "Encompasses understanding the core cloud service models, deployment models, and key "
            "concepts that form the foundation of cloud computing. Practitioners should understand "
            "IaaS (virtual machines, storage, networking), PaaS (managed databases, application "
            "platforms), and SaaS delivery models. They must be familiar with major cloud providers "
            "(AWS, Azure, GCP), core services (compute, storage, networking, identity), regions and "
            "availability zones, the shared responsibility model, and cloud pricing models including "
            "on-demand, reserved, and spot instances."
        ),
        "skills": "Cloud service models, AWS/Azure/GCP basics, virtual machines, cloud storage, cloud networking, IAM, regions/availability zones, shared responsibility, pricing models."
    },
    {
        "id": "CD-003",
        "title": "Networking and TCP/IP Protocols",
        "description": (
            "Covers the networking fundamentals essential for cloud infrastructure and DevOps work. "
            "Practitioners must understand the TCP/IP model, OSI reference model, IP addressing "
            "(IPv4/IPv6), subnetting and CIDR notation, DNS resolution, HTTP/HTTPS protocols, load "
            "balancing concepts, firewalls and security groups, VPNs, and network troubleshooting "
            "tools (ping, traceroute, netstat, nslookup, tcpdump). They should be able to design "
            "virtual private clouds (VPCs), configure subnets, route tables, and network ACLs in "
            "cloud environments."
        ),
        "skills": "TCP/IP, DNS, HTTP/HTTPS, subnetting, CIDR, VPC design, firewalls, security groups, load balancing, network troubleshooting, VPN, route tables."
    },
    {
        "id": "CD-004",
        "title": "Shell Scripting and Automation",
        "description": (
            "Focuses on writing shell scripts (Bash) and using scripting languages (Python) to "
            "automate routine system administration and operational tasks. Practitioners should be "
            "able to write scripts for log parsing, automated backups, system health checks, user "
            "provisioning, and deployment automation. They must understand variables, control "
            "structures, functions, input/output redirection, pipes, regular expressions, error "
            "handling in scripts, and how to make scripts idempotent. Automating repetitive tasks "
            "reduces human error and is a cornerstone of DevOps culture."
        ),
        "skills": "Bash scripting, Python scripting, variables, control flow, functions, pipes, redirection, regex, cron automation, idempotent scripts, error handling."
    },
    {
        "id": "CD-005",
        "title": "Containerization with Docker",
        "description": (
            "Covers the principles and practices of containerisation using Docker for packaging, "
            "distributing, and running applications in isolated environments. Practitioners must "
            "understand container concepts versus virtual machines, Docker architecture (daemon, "
            "CLI, registry), writing efficient Dockerfiles with multi-stage builds, managing images "
            "and containers, Docker networking (bridge, host, overlay), volume management for "
            "persistent data, Docker Compose for multi-container applications, and security best "
            "practices (non-root users, minimal base images, image scanning)."
        ),
        "skills": "Docker, Dockerfiles, multi-stage builds, Docker Compose, container networking, volumes, image registries, container security, docker-compose.yml, image optimisation."
    },
    {
        "id": "CD-006",
        "title": "CI/CD Pipeline Configuration",
        "description": (
            "Addresses the design and implementation of Continuous Integration and Continuous "
            "Delivery/Deployment pipelines that automate the build, test, and deployment lifecycle. "
            "Practitioners should be proficient with CI/CD tools (Jenkins, GitHub Actions, GitLab CI, "
            "CircleCI), understand pipeline stages (build, lint, test, security scan, deploy), "
            "artifact management, environment promotion strategies, rollback mechanisms, and secrets "
            "management in pipelines. They must be able to implement automated testing gates, "
            "parallelise pipeline stages, and optimise pipeline execution time."
        ),
        "skills": "Jenkins, GitHub Actions, GitLab CI, pipeline stages, automated testing, artifact management, secrets management, deployment strategies (blue-green, canary), rollback."
    },
    {
        "id": "CD-007",
        "title": "Infrastructure as Code Basics",
        "description": (
            "Covers the practice of managing and provisioning infrastructure through machine-readable "
            "configuration files rather than manual processes. Practitioners should understand "
            "declarative versus imperative approaches, be proficient with tools like Terraform and "
            "AWS CloudFormation, understand state management, resource dependencies, and modules for "
            "reusable infrastructure patterns. They must be able to write, plan, and apply "
            "infrastructure definitions, implement infrastructure testing, and follow best practices "
            "for code organisation, version control, and team collaboration on infrastructure code."
        ),
        "skills": "Terraform, CloudFormation, declarative configuration, state management, modules, resource dependencies, plan/apply workflow, infrastructure testing, HCL."
    },
    {
        "id": "CD-008",
        "title": "Version Control and Branching Strategies",
        "description": (
            "Encompasses the use of version control systems and collaborative development workflows "
            "in DevOps contexts. Practitioners must master Git operations, understand branching "
            "strategies (trunk-based development, Git Flow, GitHub Flow, release branching), implement "
            "effective code review processes, manage merge conflicts, and enforce branch protection "
            "rules. They should understand how version control integrates with CI/CD pipelines, "
            "how to manage monorepo versus polyrepo strategies, and how to use Git tags for release "
            "management."
        ),
        "skills": "Git, branching strategies, trunk-based development, code review, merge conflict resolution, branch protection, Git tags, release management, monorepo/polyrepo."
    },
    {
        "id": "CD-009",
        "title": "Monitoring and Logging",
        "description": (
            "Covers the implementation of monitoring, logging, and observability systems to ensure "
            "the health, performance, and reliability of applications and infrastructure. Practitioners "
            "should understand the three pillars of observability (metrics, logs, traces), be "
            "proficient with tools like Prometheus, Grafana, ELK Stack (Elasticsearch, Logstash, "
            "Kibana), and Datadog. They must be able to define SLIs, SLOs, and SLAs, create "
            "meaningful dashboards, configure alerting rules, implement structured logging, and "
            "perform root cause analysis using observability data."
        ),
        "skills": "Prometheus, Grafana, ELK Stack, metrics, logging, tracing, SLIs/SLOs/SLAs, dashboards, alerting, structured logging, root cause analysis, Datadog."
    },
    {
        "id": "CD-010",
        "title": "Cloud Security Fundamentals",
        "description": (
            "Addresses the essential security practices for protecting cloud infrastructure, "
            "applications, and data. Practitioners must understand identity and access management "
            "(IAM policies, roles, least privilege), network security (security groups, NACLs, WAF), "
            "data encryption (at rest and in transit), secrets management (HashiCorp Vault, AWS "
            "Secrets Manager), compliance frameworks (SOC 2, ISO 27001), vulnerability scanning, "
            "and security incident response. They should be able to implement defence-in-depth "
            "strategies and follow the shared responsibility model for cloud security."
        ),
        "skills": "IAM, least privilege, security groups, encryption, secrets management, Vault, compliance (SOC 2, ISO 27001), vulnerability scanning, WAF, incident response."
    },
    {
        "id": "CD-011",
        "title": "Kubernetes and Container Orchestration",
        "description": (
            "Covers the orchestration of containerised applications at scale using Kubernetes. "
            "Practitioners must understand Kubernetes architecture (control plane, nodes, kubelet, "
            "etcd), core objects (Pods, Deployments, Services, ConfigMaps, Secrets, Namespaces, "
            "Ingress), scaling strategies (HPA, VPA, cluster autoscaler), persistent storage "
            "(PV/PVC, StorageClasses), RBAC for Kubernetes, Helm charts for package management, and "
            "networking with CNI plugins. They should be able to deploy, manage, and troubleshoot "
            "applications on Kubernetes clusters in production environments."
        ),
        "skills": "Kubernetes, kubectl, Pods, Deployments, Services, Ingress, Helm, RBAC, HPA/VPA, PV/PVC, namespaces, CNI, cluster management, troubleshooting."
    },
    {
        "id": "CD-012",
        "title": "Service Mesh Architecture (Istio, Linkerd)",
        "description": (
            "Addresses the implementation and management of service mesh infrastructure for "
            "microservices communication. Practitioners should understand the sidecar proxy pattern, "
            "control plane vs data plane architecture, traffic management (routing, load balancing, "
            "circuit breaking, retries, timeouts), mutual TLS (mTLS) for service-to-service "
            "encryption, observability features (distributed tracing, service-level metrics), and "
            "policy enforcement. They must be familiar with Istio and Linkerd, understand when a "
            "service mesh adds value versus unnecessary complexity, and be able to diagnose mesh-"
            "related issues."
        ),
        "skills": "Istio, Linkerd, sidecar proxy, mTLS, traffic management, circuit breaking, distributed tracing, service mesh observability, policy enforcement, Envoy proxy."
    },
    {
        "id": "CD-013",
        "title": "Chaos Engineering and Reliability Testing",
        "description": (
            "Covers the discipline of proactively injecting controlled failures into systems to "
            "identify weaknesses before they cause outages. Practitioners should understand chaos "
            "engineering principles (as defined by Netflix and the Chaos Engineering community), "
            "be able to design and execute chaos experiments, use tools like Chaos Monkey, Gremlin, "
            "and Litmus Chaos, define steady-state hypotheses, blast radius limitation, and "
            "implement game days. They must also understand resilience patterns (circuit breakers, "
            "bulkheads, retries with backoff) and how chaos engineering contributes to improving "
            "system reliability."
        ),
        "skills": "Chaos Monkey, Gremlin, Litmus, chaos experiments, steady-state hypothesis, blast radius, game days, resilience patterns, circuit breakers, reliability testing."
    },
    {
        "id": "CD-014",
        "title": "GitOps and Declarative Infrastructure",
        "description": (
            "Focuses on GitOps as a paradigm for managing infrastructure and application deployments "
            "using Git as the single source of truth. Practitioners should understand GitOps "
            "principles (declarative configuration, version-controlled desired state, automated "
            "reconciliation, continuous observation), be proficient with tools like ArgoCD and "
            "Flux, understand the pull-based deployment model versus push-based CI/CD, and implement "
            "drift detection and automated remediation. They must be able to structure Git "
            "repositories for GitOps workflows and manage multi-environment deployments declaratively."
        ),
        "skills": "ArgoCD, Flux, GitOps principles, declarative configuration, automated reconciliation, drift detection, pull-based deployment, multi-environment management, Kustomize."
    },
    {
        "id": "CD-015",
        "title": "Cloud Cost Optimization and FinOps",
        "description": (
            "Addresses the strategies and practices for managing and optimising cloud spending, "
            "aligned with FinOps Foundation principles. Practitioners should understand cloud "
            "billing models, cost allocation through tagging strategies, rightsizing recommendations, "
            "reserved instance and savings plan strategies, spot/preemptible instance usage, "
            "storage tier optimisation, and cost monitoring/alerting tools (AWS Cost Explorer, "
            "Azure Cost Management, GCP Billing). They must be able to create cost dashboards, "
            "forecast spending, implement automated cost controls, and communicate cloud costs to "
            "business stakeholders."
        ),
        "skills": "FinOps, cost allocation, tagging strategies, rightsizing, reserved instances, spot instances, cost monitoring, AWS Cost Explorer, budgets, automated cost controls."
    },
]

# ============================================================================
# SYLLABUS DATA
# ============================================================================

DS_SYLLABUS = {
    "title": "BSc Data Science - Semester 5 Syllabus",
    "university": "National Institute of Technology (Autonomous)",
    "program": "Bachelor of Science in Data Science",
    "semester": "Semester V",
    "year": "2024-25",
    "credits": 24,
    "units": [
        {
            "name": "Unit 1: Foundations of Statistical Analysis",
            "hours": 15,
            "marks": 20,
            "topics": [
                "1.1 Descriptive Statistics: Measures of central tendency and dispersion",
                "1.2 Probability Distributions: Normal, Binomial, Poisson distributions",
                "1.3 Hypothesis Testing: Null and alternative hypotheses, p-values",
                "1.4 Parametric Tests: t-test, z-test, ANOVA, F-test",
                "1.5 Non-Parametric Tests: Chi-square, Mann-Whitney U, Kruskal-Wallis",
                "1.6 Confidence Intervals and Effect Size Estimation",
                "1.7 Bayesian vs Frequentist Approaches to Inference",
                "1.8 Probability Axioms, Conditional Probability and Bayes' Theorem",
            ]
        },
        {
            "name": "Unit 2: Data Wrangling and Exploratory Analysis",
            "hours": 15,
            "marks": 20,
            "topics": [
                "2.1 Data Collection Methods and Data Quality Assessment",
                "2.2 Handling Missing Values: Imputation techniques (mean, median, KNN, MICE)",
                "2.3 Outlier Detection and Treatment (IQR, Z-score methods)",
                "2.4 Feature Scaling: Standardisation, Min-Max Normalisation",
                "2.5 Categorical Encoding: One-hot, Label, Target, and Ordinal Encoding",
                "2.6 Exploratory Data Analysis (EDA): Summary statistics and profiling",
                "2.7 Correlation Analysis, Pair Plots, Distribution Visualisation",
                "2.8 Feature Engineering and Transformation Pipelines",
            ]
        },
        {
            "name": "Unit 3: Data Visualization and Database Systems",
            "hours": 15,
            "marks": 20,
            "topics": [
                "3.1 Principles of Effective Data Visualisation",
                "3.2 Matplotlib: Line plots, bar charts, histograms, scatter plots",
                "3.3 Seaborn: Statistical visualisations, heatmaps, violin plots",
                "3.4 Interactive Visualisation with Plotly and Dash",
                "3.5 Dashboard Design Principles and Storytelling with Data",
                "3.6 Relational Database Concepts and Normalisation (1NF-3NF)",
                "3.7 SQL: SELECT, JOIN, GROUP BY, Subqueries, Window Functions, CTEs",
                "3.8 Database Indexing, Transactions, and Connection Management",
            ]
        },
        {
            "name": "Unit 4: Python Programming and Mathematical Foundations",
            "hours": 15,
            "marks": 20,
            "topics": [
                "4.1 Python Core: Data structures, control flow, functions, OOP",
                "4.2 NumPy: Arrays, broadcasting, linear algebra operations",
                "4.3 Pandas: DataFrames, Series, groupby, merge, pivot tables",
                "4.4 Linear Algebra: Vectors, Matrices, Eigenvalues, SVD",
                "4.5 Calculus: Derivatives, Partial Derivatives, Gradient Descent",
                "4.6 Optimisation: Cost functions, convexity, learning rate",
                "4.7 Jupyter Notebooks and Reproducible Analysis",
                "4.8 Virtual Environments, Package Management, and Code Standards",
            ]
        },
        {
            "name": "Unit 5: Machine Learning and Regression Methods",
            "hours": 15,
            "marks": 20,
            "topics": [
                "5.1 Supervised Learning: Concepts, training/test splits, bias-variance",
                "5.2 Linear Regression: OLS, assumptions, residual analysis",
                "5.3 Logistic Regression: Sigmoid function, MLE, odds ratios",
                "5.4 Regularisation: L1 (Lasso), L2 (Ridge), Elastic Net",
                "5.5 Decision Trees and Random Forests",
                "5.6 Support Vector Machines and Kernel Methods",
                "5.7 Model Evaluation: Accuracy, Precision, Recall, F1-score, AUC-ROC",
                "5.8 Cross-Validation, Hyperparameter Tuning (Grid Search, Random Search)",
            ]
        },
    ]
}

WD_SYLLABUS = {
    "title": "BSc IT - Web Development Specialization Syllabus",
    "university": "Mumbai University (Autonomous)",
    "program": "Bachelor of Science in Information Technology",
    "semester": "Semester V & VI - Web Development Specialization",
    "year": "2024-25",
    "credits": 28,
    "units": [
        {
            "name": "Unit 1: HTML5, CSS3, and Responsive Web Design",
            "hours": 18,
            "marks": 25,
            "topics": [
                "1.1 HTML5 Semantic Elements: header, nav, main, article, section, aside, footer",
                "1.2 HTML Forms: Input types, validation, accessibility labels, ARIA roles",
                "1.3 CSS3 Fundamentals: Selectors, specificity, cascade, inheritance",
                "1.4 Box Model, Flexbox Layout, CSS Grid Layout",
                "1.5 Responsive Design: Media queries, mobile-first approach, fluid grids",
                "1.6 CSS Variables, SASS/SCSS Preprocessor",
                "1.7 CSS Animations, Transitions, and Transforms",
                "1.8 Responsive Images and Typography",
            ]
        },
        {
            "name": "Unit 2: JavaScript ES6+ and DOM Programming",
            "hours": 18,
            "marks": 25,
            "topics": [
                "2.1 JavaScript ES6+ Syntax: let/const, arrow functions, template literals",
                "2.2 Destructuring, Spread/Rest Operators, Default Parameters",
                "2.3 Promises, Async/Await, and the Event Loop",
                "2.4 ES6 Modules: import/export, module bundlers (Webpack, Vite)",
                "2.5 Closures, Prototypal Inheritance, and Higher-Order Functions",
                "2.6 DOM Traversal and Manipulation Methods",
                "2.7 Event Handling, Event Delegation, and Custom Events",
                "2.8 Browser APIs: Fetch, localStorage, Intersection Observer, History API",
            ]
        },
        {
            "name": "Unit 3: React.js and Modern Frontend Architecture",
            "hours": 18,
            "marks": 25,
            "topics": [
                "3.1 React Fundamentals: JSX, Components, Props, and State",
                "3.2 Hooks: useState, useEffect, useContext, useReducer, useMemo, useCallback",
                "3.3 Component Composition and Conditional Rendering",
                "3.4 State Management: Context API, Redux Toolkit, Zustand",
                "3.5 React Router: Client-side routing and navigation",
                "3.6 Form Handling and Validation in React",
                "3.7 Performance Optimisation: React.memo, useMemo, code splitting",
                "3.8 Testing React Components: Jest, React Testing Library",
            ]
        },
        {
            "name": "Unit 4: Server-Side Development with Node.js",
            "hours": 18,
            "marks": 25,
            "topics": [
                "4.1 Node.js Architecture: Event-driven, non-blocking I/O model",
                "4.2 Express.js: Routing, middleware, request/response handling",
                "4.3 RESTful API Design: HTTP methods, status codes, resource naming",
                "4.4 API Documentation with OpenAPI/Swagger",
                "4.5 Authentication: JWT tokens, session management, OAuth 2.0 basics",
                "4.6 Authorization: Role-based access control (RBAC), route protection",
                "4.7 Password Security: bcrypt hashing, CSRF/XSS prevention",
                "4.8 Error Handling, Logging, and Environment Configuration",
            ]
        },
        {
            "name": "Unit 5: Databases, Version Control, and Deployment Basics",
            "hours": 18,
            "marks": 25,
            "topics": [
                "5.1 Relational Database Design: ER modelling, normalisation (1NF-3NF)",
                "5.2 SQL: Queries, JOINs, aggregations, indexing, transactions",
                "5.3 ORMs: Sequelize / Prisma for Node.js applications",
                "5.4 Database Migrations and Connection Pooling",
                "5.5 Git Fundamentals: Commits, branches, merges, rebases",
                "5.6 Branching Strategies: Git Flow, GitHub Flow, feature branching",
                "5.7 Pull Requests, Code Review, and Merge Conflict Resolution",
                "5.8 Basic Deployment: Static hosting, environment variables, npm scripts",
            ]
        },
    ]
}

CD_SYLLABUS = {
    "title": "BSc CS - Cloud Computing and DevOps Syllabus",
    "university": "Pune University (Autonomous)",
    "program": "Bachelor of Science in Computer Science",
    "semester": "Semester V & VI - Cloud Computing and DevOps Elective",
    "year": "2024-25",
    "credits": 26,
    "units": [
        {
            "name": "Unit 1: Linux Administration and Networking Fundamentals",
            "hours": 18,
            "marks": 25,
            "topics": [
                "1.1 Linux Filesystem Navigation and File Management",
                "1.2 User and Group Management, File Permissions (chmod, chown)",
                "1.3 Package Management (apt, yum, dnf) and systemd Services",
                "1.4 Process Management, System Monitoring (top, htop, vmstat)",
                "1.5 TCP/IP Model and OSI Reference Layers",
                "1.6 IP Addressing, Subnetting, CIDR Notation",
                "1.7 DNS Resolution, HTTP/HTTPS Protocols",
                "1.8 Network Troubleshooting: ping, traceroute, netstat, nslookup, tcpdump",
            ]
        },
        {
            "name": "Unit 2: Cloud Computing Fundamentals",
            "hours": 18,
            "marks": 25,
            "topics": [
                "2.1 Cloud Service Models: IaaS, PaaS, SaaS",
                "2.2 Cloud Deployment Models: Public, Private, Hybrid, Multi-cloud",
                "2.3 Major Cloud Providers: AWS, Azure, GCP Overview",
                "2.4 Core Cloud Services: Compute (EC2, VMs), Storage (S3, Blob), Networking",
                "2.5 Identity and Access Management (IAM): Policies, Roles, Least Privilege",
                "2.6 Regions, Availability Zones, and the Shared Responsibility Model",
                "2.7 Cloud Security Fundamentals: Security Groups, NACLs, Encryption",
                "2.8 Secrets Management: HashiCorp Vault, AWS Secrets Manager",
            ]
        },
        {
            "name": "Unit 3: Shell Scripting and Automation",
            "hours": 15,
            "marks": 20,
            "topics": [
                "3.1 Bash Scripting: Variables, Control Structures, Functions",
                "3.2 Input/Output Redirection, Pipes, and Filters",
                "3.3 Regular Expressions and Text Processing (grep, sed, awk)",
                "3.4 Automation Scripts: Log parsing, backups, health checks",
                "3.5 Python for DevOps: Automating infrastructure tasks",
                "3.6 Idempotent Scripts and Error Handling Patterns",
                "3.7 Cron Jobs and Scheduled Task Management",
                "3.8 Configuration Management Basics (Ansible introduction)",
            ]
        },
        {
            "name": "Unit 4: Containerization with Docker",
            "hours": 18,
            "marks": 25,
            "topics": [
                "4.1 Container Concepts: Containers vs Virtual Machines",
                "4.2 Docker Architecture: Daemon, CLI, Registry",
                "4.3 Dockerfiles: Instructions, Best Practices, Multi-stage Builds",
                "4.4 Image Management: Building, Tagging, Pushing, and Pulling",
                "4.5 Docker Networking: Bridge, Host, Overlay Networks",
                "4.6 Volume Management for Persistent Data",
                "4.7 Docker Compose: Multi-container Application Definitions",
                "4.8 Container Security: Non-root users, minimal images, scanning",
            ]
        },
        {
            "name": "Unit 5: CI/CD, Infrastructure as Code, and Monitoring",
            "hours": 18,
            "marks": 25,
            "topics": [
                "5.1 CI/CD Concepts: Continuous Integration, Delivery, and Deployment",
                "5.2 Pipeline Tools: Jenkins, GitHub Actions, GitLab CI",
                "5.3 Pipeline Stages: Build, Lint, Test, Security Scan, Deploy",
                "5.4 Deployment Strategies: Blue-green, Canary, Rolling updates",
                "5.5 Infrastructure as Code: Terraform basics, HCL syntax",
                "5.6 Terraform Workflow: init, plan, apply, state management",
                "5.7 Version Control for DevOps: Git, branching strategies, tags",
                "5.8 Monitoring and Logging: Prometheus, Grafana, ELK Stack, SLIs/SLOs",
            ]
        },
    ]
}


# ============================================================================
# PDF GENERATION FUNCTIONS
# ============================================================================

def create_framework_pdf(filepath, domain, attribution, competencies):
    """Generate a multi-page framework PDF with detailed competency descriptions."""
    sections = []

    # Title page content
    sections.append({
        "text": f"{domain} Competency Framework",
        "fontsize": 20,
        "fontname": "hebo",
        "color": (0.1, 0.1, 0.5),
        "spacing_before": 20,
    })
    sections.append({
        "text": f"Industry-Standard Competency Framework for {domain}",
        "fontsize": 12,
        "fontname": "hebi",
        "color": (0.3, 0.3, 0.3),
        "spacing_before": 8,
    })
    sections.append({
        "text": f"Source: {attribution}",
        "fontsize": 9,
        "fontname": "hebo",
        "color": (0.4, 0.4, 0.4),
        "spacing_before": 6,
    })
    sections.append({
        "text": (
            f"This framework defines the essential competencies expected of professionals in "
            f"{domain}. It is intended for use by educational institutions to evaluate curriculum "
            f"coverage, identify gaps, and align academic programs with industry expectations. "
            f"Each competency includes a unique identifier, detailed description, and required "
            f"skill areas."
        ),
        "fontsize": 10,
        "fontname": "helv",
        "color": (0.2, 0.2, 0.2),
        "spacing_before": 14,
    })
    sections.append({
        "text": f"Total Competencies: {len(competencies)}",
        "fontsize": 11,
        "fontname": "hebo",
        "color": (0, 0, 0),
        "spacing_before": 12,
    })

    # Separator
    sections.append({
        "text": "=" * 70,
        "fontsize": 8,
        "fontname": "helv",
        "color": (0.6, 0.6, 0.6),
        "spacing_before": 10,
    })

    # Competency entries
    for comp in competencies:
        sections.append({
            "text": f"Competency {comp['id']}: {comp['title']}",
            "fontsize": 13,
            "fontname": "hebo",
            "color": (0.05, 0.15, 0.45),
            "spacing_before": 18,
        })
        sections.append({
            "text": f"[ID: {comp['id']}]",
            "fontsize": 9,
            "fontname": "hebo",
            "color": (0.4, 0.4, 0.4),
            "spacing_before": 4,
        })
        sections.append({
            "text": "Description:",
            "fontsize": 10,
            "fontname": "hebo",
            "color": (0, 0, 0),
            "spacing_before": 6,
        })
        sections.append({
            "text": comp["description"],
            "fontsize": 10,
            "fontname": "helv",
            "color": (0.1, 0.1, 0.1),
            "spacing_before": 3,
            "indent": 10,
        })
        sections.append({
            "text": "Required Skills:",
            "fontsize": 10,
            "fontname": "hebo",
            "color": (0, 0, 0),
            "spacing_before": 8,
        })
        sections.append({
            "text": comp["skills"],
            "fontsize": 10,
            "fontname": "helv",
            "color": (0.1, 0.1, 0.1),
            "spacing_before": 3,
            "indent": 10,
        })
        # Separator between competencies
        sections.append({
            "text": "-" * 60,
            "fontsize": 7,
            "fontname": "helv",
            "color": (0.75, 0.75, 0.75),
            "spacing_before": 8,
        })

    create_pdf(filepath, sections)


def create_syllabus_pdf(filepath, syllabus_data):
    """Generate a realistic university syllabus PDF."""
    sections = []

    # Header
    sections.append({
        "text": syllabus_data["university"],
        "fontsize": 16,
        "fontname": "hebo",
        "color": (0.1, 0.1, 0.4),
        "spacing_before": 10,
    })
    sections.append({
        "text": syllabus_data["program"],
        "fontsize": 13,
        "fontname": "hebo",
        "color": (0.2, 0.2, 0.2),
        "spacing_before": 6,
    })
    sections.append({
        "text": syllabus_data["title"],
        "fontsize": 14,
        "fontname": "hebo",
        "color": (0.05, 0.15, 0.45),
        "spacing_before": 8,
    })
    sections.append({
        "text": f"{syllabus_data['semester']} | Academic Year: {syllabus_data['year']} | Total Credits: {syllabus_data['credits']}",
        "fontsize": 10,
        "fontname": "helv",
        "color": (0.3, 0.3, 0.3),
        "spacing_before": 6,
    })

    # Course objectives
    sections.append({
        "text": "Course Objectives:",
        "fontsize": 11,
        "fontname": "hebo",
        "color": (0, 0, 0),
        "spacing_before": 14,
    })
    sections.append({
        "text": (
            "This course aims to provide students with comprehensive theoretical knowledge and "
            "practical skills in the core areas of the discipline. Upon completion, students will "
            "be able to apply fundamental concepts to solve real-world problems, demonstrate "
            "proficiency in industry-standard tools and techniques, and be prepared for advanced "
            "study or professional roles."
        ),
        "fontsize": 10,
        "fontname": "helv",
        "color": (0.15, 0.15, 0.15),
        "spacing_before": 4,
        "indent": 10,
    })

    sections.append({
        "text": "=" * 70,
        "fontsize": 8,
        "fontname": "helv",
        "color": (0.6, 0.6, 0.6),
        "spacing_before": 10,
    })

    # Units
    for unit in syllabus_data["units"]:
        sections.append({
            "text": unit["name"],
            "fontsize": 12,
            "fontname": "hebo",
            "color": (0.05, 0.15, 0.45),
            "spacing_before": 16,
        })
        sections.append({
            "text": f"Lecture Hours: {unit['hours']} | Marks: {unit['marks']}",
            "fontsize": 9,
            "fontname": "hebo",
            "color": (0.4, 0.4, 0.4),
            "spacing_before": 4,
        })

        for topic in unit["topics"]:
            sections.append({
                "text": f"  {topic}",
                "fontsize": 10,
                "fontname": "helv",
                "color": (0.1, 0.1, 0.1),
                "spacing_before": 3,
                "indent": 15,
            })

        sections.append({
            "text": "-" * 50,
            "fontsize": 7,
            "fontname": "helv",
            "color": (0.75, 0.75, 0.75),
            "spacing_before": 6,
        })

    # Assessment scheme
    sections.append({
        "text": "Assessment Scheme:",
        "fontsize": 12,
        "fontname": "hebo",
        "color": (0, 0, 0),
        "spacing_before": 16,
    })
    total_marks = sum(u["marks"] for u in syllabus_data["units"])
    sections.append({
        "text": (
            f"Internal Assessment: 40% (Assignments, Quizzes, Lab Work)\n"
            f"End Semester Examination: 60% (Written Exam: {total_marks} marks)\n"
            f"Minimum Passing: 40% aggregate with minimum 35% in each component"
        ),
        "fontsize": 10,
        "fontname": "helv",
        "color": (0.15, 0.15, 0.15),
        "spacing_before": 4,
        "indent": 10,
    })

    # References
    sections.append({
        "text": "Recommended References:",
        "fontsize": 11,
        "fontname": "hebo",
        "color": (0, 0, 0),
        "spacing_before": 14,
    })
    sections.append({
        "text": (
            "1. Official documentation and guides for all tools and technologies covered.\n"
            "2. Peer-reviewed textbooks recommended by the department.\n"
            "3. Open educational resources and MOOCs for supplementary learning."
        ),
        "fontsize": 10,
        "fontname": "helv",
        "color": (0.15, 0.15, 0.15),
        "spacing_before": 4,
        "indent": 10,
    })

    create_pdf(filepath, sections)


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("Creating Framework and Syllabus PDFs")
    print("=" * 60)

    # --- Frameworks ---
    print("\n--- Framework PDFs ---")
    create_framework_pdf(
        os.path.join(FRAMEWORK_DIR, "data_science_framework.pdf"),
        "Data Science",
        "Curated from NIST NICE Framework (Public Domain) and ESCO Classification (CC BY 4.0)",
        DS_COMPETENCIES,
    )
    create_framework_pdf(
        os.path.join(FRAMEWORK_DIR, "web_development_framework.pdf"),
        "Web Development",
        "Curated from ESCO Classification (CC BY 4.0) and ACM CS2023 Curricula Guidelines",
        WD_COMPETENCIES,
    )
    create_framework_pdf(
        os.path.join(FRAMEWORK_DIR, "cloud_devops_framework.pdf"),
        "Cloud and DevOps",
        "Curated from NIST NICE Framework (Public Domain) and ESCO Classification (CC BY 4.0)",
        CD_COMPETENCIES,
    )

    # --- Syllabi ---
    print("\n--- Syllabus PDFs ---")
    create_syllabus_pdf(
        os.path.join(SYLLABUS_DIR, "data_science.pdf"),
        DS_SYLLABUS,
    )
    create_syllabus_pdf(
        os.path.join(SYLLABUS_DIR, "web_development.pdf"),
        WD_SYLLABUS,
    )
    create_syllabus_pdf(
        os.path.join(SYLLABUS_DIR, "cloud_devops.pdf"),
        CD_SYLLABUS,
    )

    print("\n" + "=" * 60)
    print("All PDFs created successfully!")
    print("=" * 60)

    # Verify files
    print("\nVerification:")
    expected = [
        os.path.join(FRAMEWORK_DIR, "data_science_framework.pdf"),
        os.path.join(FRAMEWORK_DIR, "web_development_framework.pdf"),
        os.path.join(FRAMEWORK_DIR, "cloud_devops_framework.pdf"),
        os.path.join(SYLLABUS_DIR, "data_science.pdf"),
        os.path.join(SYLLABUS_DIR, "web_development.pdf"),
        os.path.join(SYLLABUS_DIR, "cloud_devops.pdf"),
    ]
    for f in expected:
        if os.path.exists(f):
            size_kb = os.path.getsize(f) / 1024
            doc = fitz.open(f)
            pages = doc.page_count
            doc.close()
            print(f"  OK  {os.path.basename(f):45s} {pages:>3} pages  {size_kb:>6.1f} KB")
        else:
            print(f"  MISSING  {f}")


if __name__ == "__main__":
    main()
