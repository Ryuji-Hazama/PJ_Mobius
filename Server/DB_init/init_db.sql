CREATE DATABASE IF NOT EXISTS MobiusDB;
USE MobiusDB;

CREATE TABLE IF NOT EXISTS ContractLevel (
    level_id INT AUTO_INCREMENT PRIMARY KEY,
    level_name VARCHAR(50) NOT NULL UNIQUE,
    level_description TEXT
);

CREATE TABLE IF NOT EXISTS ContractCompanies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL UNIQUE,
    company_phone VARCHAR(20),
    company_zip_code VARCHAR(10),
    company_address TEXT,
    company_email VARCHAR(100),
    contract_level INT,
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_level) REFERENCES ContractLevel(level_id)
);

CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    initial_password TINYINT NOT NULL DEFAULT 1,
    access_level ENUM('super', 'admin', 'user', 'guest') DEFAULT 'user',
    company_id INT,
    login_failed INT DEFAULT 0,
    login_failed_at TIMESTAMP,
    user_status ENUM('active', 'inactive', 'suspended') DEFAULT 'inactive',
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES ContractCompanies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (created_user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT,
    employee_code VARCHAR(20) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    code_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    hire_date DATE,
    job_title VARCHAR(100),
    department VARCHAR(100),
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_company_employee UNIQUE (company_id, employee_code),
    FOREIGN KEY (company_id) REFERENCES ContractCompanies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (created_user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Projects (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    project_description TEXT,
    company_id INT,
    contractor_id INT,
    contract_level INT,
    primary_contract_project_id INT,
    start_date DATE,
    end_date DATE,
    status ENUM('planned', 'in_progress', 'completed', 'on_hold') DEFAULT 'planned',
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES ContractCompanies(company_id),
    FOREIGN KEY (contractor_id) REFERENCES ContractCompanies(company_id),
    FOREIGN KEY (contract_level) REFERENCES ContractLevel(level_id),
    FOREIGN KEY (primary_contract_project_id) REFERENCES Projects(project_id) ON DELETE SET NULL,
    FOREIGN KEY (created_user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Contracts (
    contract_id INT NOT NULL,
    contract_employee_id INT NOT NULL,
    project_id INT,
    contract_fee INT,
    contract_start_date DATE,
    contract_end_date DATE,
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (created_user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ComputerLanguageTypes (
    type_id INT NOT NULL,
    root_id INT NOT NULL,
    parent_id INT NOT NULL,
    type_name VARCHAR(50) NOT NULL,
    type_description TEXT,
    CONSTRAINT pk_language_type PRIMARY KEY (type_id),
    CONSTRAINT uq_root_parent UNIQUE (root_id, parent_id)
);

CREATE TABLE IF NOT EXISTS ComputerLanguages (
    language_id INT AUTO_INCREMENT PRIMARY KEY,
    language_name VARCHAR(50) NOT NULL UNIQUE,
    language_description TEXT,
    type_id INT,
    created_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_user_id INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES ComputerLanguageTypes(type_id),
    FOREIGN KEY (created_user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (updated_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS SessionInfo (
    session_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    session_uuid VARCHAR(36) NOT NULL DEFAULT (UUID()),
    user_id INT,
    user_name VARCHAR(50) NOT NULL,
    company_id INT,
    access_level ENUM('super', 'admin', 'user', 'guest') NOT NULL,
    login_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    logout_datetime TIMESTAMP NOT NULL DEFAULT (ADDTIME(CURRENT_TIMESTAMP, "00:30:00")),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (company_id) REFERENCES ContractCompanies(company_id) ON DELETE SET NULL
);

-- Insert initial data into ContractLevel
-- Primary to Tertiary for project contracts
-- Community for community companies with no access
-- Partner for partner companies with special privileges

INSERT INTO ContractLevel VALUES
(1, 'Primary', 'Primary contract level with no access.'),
(2, 'Secondary', 'Secondary contract level with no access.'),
(3, 'Tertiary', 'Tertiary contract level with no access.'),
(4, 'Community', 'Community contract level with no access.'),
(5, 'Partner', 'Partner contract level with special privileges.');

-- Insert initial data into ComputerLanguageTypes

INSERT INTO ComputerLanguageTypes VALUES
(0, 0, 0, 'Root', 'The root of all programming language types.'),
(1, 1, 0, 'Low Level Languages', 'Languages that provide little or no abstraction from a computer''s instruction set architecture.'),
(2, 1, 1, 'Assembly Language', 'A low-level programming language that uses symbolic code and is specific to a computer architecture.'),
(3, 1, 2, 'Machine Code', 'The lowest-level programming language, consisting of binary code that the computer''s CPU can execute directly.'),
(4, 2, 0, 'High Level Languages', 'Languages that provide strong abstraction from the details of the computer.'),
(5, 2, 1, 'Procedural Languages', 'Languages that are based on the concept of procedure calls.'),
(6, 2, 2, 'Object-Oriented Languages', 'Languages that are based on the concept of "objects", which can contain data and code.'),
(7, 2, 3, 'Functional Languages', 'Languages that treat computation as the evaluation of mathematical functions and avoid changing state and mutable data.'),
(8, 2, 4, 'Scripting Languages', 'Languages that are often interpreted and used for automating tasks.'),
(9, 3, 0, 'Specialized Languages', 'Languages designed for specific tasks or domains.'),
(10, 3, 1, 'Query Languages', 'Languages used to make queries in databases and information systems.'),
(11, 3, 2, 'Markup Languages', 'Languages used to annotate text so that the computer can manipulate it.'),
(12, 3, 3, 'Domain-Specific Languages', 'Languages tailored to a specific application domain.'),
(13, 4, 0, 'Other Languages', 'Languages that do not fit into the above categories.'),
(14, 4, 1, 'Visual Programming Languages', 'Languages that allow users to create programs by manipulating program elements graphically rather than by specifying them textually.'),
(15, 4, 2, 'Concurrent Languages', 'Languages designed to handle concurrent programming and parallel processing.'),
(16, 4, 3, 'Esoteric Languages', 'Languages created as a joke or to experiment with unusual concepts.'),
(99, 4, 99, 'Uncategorized', 'Languages that have not been categorized yet.'),
(100, 0, 1, 'Other skills', 'Skills that do not fit into the programming language categories.');

-- Insert initial data into ComputerLanguages

INSERT INTO ComputerLanguages (language_name, language_description, type_id) VALUES
('C', 'A general-purpose programming language that is widely used for system and application software.', 5),
('C++', 'An extension of the C programming language that includes object-oriented features.', 6),
('Java', 'A high-level, class-based, object-oriented programming language that is designed to have as few implementation dependencies as possible.', 6),
('Python', 'An interpreted, high-level, general-purpose programming language that emphasizes code readability. This system is developed using Python, by the way.', 6),
('JavaScript', 'A high-level, often just-in-time compiled language that conforms to the ECMAScript specification and is widely used for web development.', 8),
('Ruby', 'A dynamic, open source programming language with a focus on simplicity and productivity.', 7),
('PHP', 'A popular general-purpose scripting language that is especially suited to web development.', 8),
('Swift', 'A powerful and intuitive programming language for macOS, iOS, watchOS, and tvOS.', 6),
('Go', 'A statically typed, compiled programming language designed at Google that is syntactically similar to C.', 5),
('Rust', 'A multi-paradigm programming language focused on performance and safety, particularly safe concurrency.', 5),
('SQL', 'A domain-specific language used in programming and designed for managing data held in a relational database management system.', 10),
('HTML', 'The standard markup language for documents designed to be displayed in a web browser.', 11),
('CSS', 'A style sheet language used for describing the presentation of a document written in HTML or XML.', 11),
('Markdown', 'A lightweight markup language with plain text formatting syntax designed to be converted to HTML and many other formats.', 11),
('Racket', 'A general-purpose, multi-paradigm programming language in the Lisp-Scheme family.', 7),
('Julia', 'A high-level, high-performance dynamic programming language for technical computing.', 7),
('R', 'A programming language and free software environment for statistical computing and graphics supported by the R Foundation for Statistical Computing.', 7),
('MATLAB', 'A multi-paradigm numerical computing environment and proprietary programming language developed by MathWorks.', 9),
('Perl', 'A family of two high-level, general-purpose, interpreted, dynamic programming languages.', 8),
('Kotlin', 'A cross-platform, statically typed, general-purpose programming language with type inference.', 6),
('TypeScript', 'An open-source language which builds on JavaScript by adding static type definitions.', 8),
('Scala', 'A strong static type general-purpose programming language which supports both object-oriented programming and functional programming.', 6),
('Haskell', 'A general-purpose, statically typed, purely functional programming language with type inference and lazy evaluation.', 7),
('Lua', 'A lightweight, high-level, multi-paradigm programming language designed primarily for embedded use in applications.', 8),
('Dart', 'A client-optimized programming language for apps on multiple platforms, developed by Google.', 6),
('Elixir', 'A dynamic, functional language designed for building scalable and maintainable applications.', 7),
('C#', 'A modern, object-oriented programming language developed by Microsoft as part of its .NET initiative.', 6),
('Visual Basic .NET', 'An object-oriented programming language implemented on the .NET Framework.', 6),
('VBA(Excel)', 'A programming language developed by Microsoft that is primarily used for automating tasks in Microsoft Office applications.', 8),
('VBA(Access)', 'A programming language developed by Microsoft that is primarily used for automating tasks in Microsoft Office applications.', 8),
('VBScript', 'An Active Scripting language developed by Microsoft that is modeled on Visual Basic.', 8),
('Objective-C', 'A general-purpose, object-oriented programming language that adds Smalltalk-style messaging to the C programming language.', 6),
('Pascal', 'An imperative and procedural programming language, designed as a small, efficient language intended to encourage good programming practices using structured programming and data structuring.', 5),
('Delphi', 'A high-level, compiled, strongly typed language that supports structured and object-oriented design.', 6),
('F#', 'A functional-first programming language that also supports imperative and object-oriented programming.', 7),
('COBOL', 'A compiled English-like computer programming language designed for business use.', 5),
('Fortran', 'A general-purpose, compiled imperative programming language that is especially suited to numeric computation and scientific computing.', 5),
('Ada', 'A structured, statically typed, imperative, and object-oriented high-level computer programming language, extended from Pascal and other languages.', 5),
('Lisp', 'A family of programming languages with a long history and a distinctive, fully parenthesized prefix notation.', 7),
('Prolog', 'A logic programming language associated with artificial intelligence and computational linguistics.', 9),
('Scheme', 'A minimalist dialect of the Lisp family of programming languages.', 7),
('Erlang', 'A general-purpose, concurrent, functional programming language, and a garbage-collected runtime system.', 7),
('Groovy', 'An object-oriented programming language for the Java platform that is dynamically compiled to Java Virtual Machine (JVM) bytecode.', 8),
('Shell Scripting', 'A script written for the shell, or command line interpreter, of an operating system.', 8),
('PowerShell', 'A task automation and configuration management framework from Microsoft, consisting of a command-line shell and associated scripting language.', 8),
('Assembly Language (x86)', 'A low-level programming language for the x86 family of microprocessors.', 2),
('Assembly Language (ARM)', 'A low-level programming language for the ARM family of microprocessors.', 2),
('Intel 8080/8085 Assembly', 'Assembly language for the Intel 8080/8085 microprocessor.', 2),
('Z80 Assembly', 'Assembly language for the Zilog Z80 microprocessor.', 2),
('Machine Code (x86)', 'The binary code that the x86 family of microprocessors can execute directly.', 3),
('Machine Code (ARM)', 'The binary code that the ARM family of microprocessors can execute directly.', 3),
('Other skills', 'Skills that do not fit into the programming language categories.', 100);

-- REVOKE ALL PRIVILEGES ON MobiusDB.* FROM 'mobius'@'%';
-- GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.* TO 'mobius'@'localhost';
-- REVOKE DELETE ON MobiusDB.SessionInfo FROM 'mobius';
-- REVOKE ALL PRIVILEGES ON MobiusDB.ContractLevel FROM 'mobius';
-- GRANT SELECT ON MobiusDB.ContractLevel FROM 'mobius'@'localhost';