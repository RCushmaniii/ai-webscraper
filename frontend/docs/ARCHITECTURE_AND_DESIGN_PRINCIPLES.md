---
title: "Architecture and Design Principles"
summary: "Outlines the core principles and architectural standards for the e-commerce platform, crucial for building a secure, scalable, and maintainable application."
---

# Architecture and Design Principles

This document outlines the core principles and architectural standards for our e-commerce platform. Adhering to these guidelines is crucial for building a secure, scalable, maintainable, and high-performance application. All developers should be familiar with these concepts and apply them during development and code reviews.

---

## 1. Core Coding Principles

These are the foundational, non-negotiable principles that apply to all code in our repository.

### Single Responsibility Principle (SRP)
Each file, function, or class should have only one specific responsibility and therefore only one reason to change. For example, a component should handle UI rendering, while a separate service handles data fetching.

### DRY (Don't Repeat Yourself)
Avoid redundant code. If you find yourself writing the same logic in multiple places, abstract it into a reusable unit (e.g., a custom hook, utility function, or service).

### Separation of Concerns (SoC)
Ensure a clear distinction between different layers of the application:
* **UI/View Layer:** React components responsible for rendering UI.
* **Logic/State Layer:** Custom hooks or state management for business logic.
* **Data Layer:** Services dedicated to communicating with Supabase and other APIs.

### SOLID Principles
Beyond SRP, our code should adhere to the other SOLID principles to remain flexible and robust:
* **(O) Open/Closed:** Modules should be open for extension but closed for modification.
* **(L) Liskov Substitution:** Subtypes must be substitutable for their base types.
* **(I) Interface Segregation:** Don't force clients to depend on interfaces they don't use (e.g., keep component props minimal).
* **(D) Dependency Inversion:** High-level modules should depend on abstractions, not low-level implementations (e.g., components call a `useAuth` hook, not Supabase directly).

---

## 2. Project-Specific Directives

These are tactical guidelines tailored to our specific technology stack (Next.js, React, Supabase).

### Security & Supabase Integration 🛡️
* **Enforce Server-Side Logic:** All database mutations (creates, updates, deletes) must be handled on the server using Next.js **Server Actions** or **Route Handlers**. Do not trust the client.
* **Use Row Level Security (RLS):** Ensure all Supabase queries are compatible with **Row Level Security (RLS)**. Queries must filter data based on the authenticated user's permissions.
* **Leverage Official Libraries:** Use the `@supabase/ssr` package for all server-side authentication and session management.
* **Sanitize Inputs:** Always validate and sanitize user input on the server before database operations to prevent XSS and SQL injection attacks.

### Next.js Architecture & Performance 🚀
* **Server Components First:** Default to **React Server Components (RSCs)** for data fetching and non-interactive UI. Only use a Client Component (`'use client'`) when client-side interactivity is required.
* **Efficient Data Fetching:** Implement appropriate caching strategies. Use Next.js `revalidate` tags or time-based revalidation for data that changes infrequently.
* **Middleware for Guarding Routes:** Use Next.js **Middleware** to protect routes and handle redirects based on authentication status.

### E-commerce & Multi-Tenant Design 🏪
* **Design for Multi-Tenancy:** This is a multi-tenant application. All database schemas and queries must be designed to isolate data for each customer's store (e.g., every `products` table must have a `store_id` column, and queries must filter by it).
* **Prioritize Accessibility (a11y):** Generate semantic HTML and ensure all interactive components are fully accessible, including proper ARIA attributes for elements like modals, dropdowns, and forms.

---

## 3. How to Use This Document

This is a living document. It should be:
* A required read for any new developer joining the project.
* Referenced during Pull Request (PR) reviews to ensure standards are being met.
* Updated as our team and technology evolve.

---

## 4. Prompting AI for Code Generation 🤖

To ensure any AI assistant generates code that aligns with our architecture, use the following conversational workflow. This approach helps you and the AI discover the necessary context and build a solution step-by-step.

### Step 1: State the Goal & Ask for Analysis
Start by describing your high-level goal and ask the AI to act as an architect. Request a list of questions or potentially affected files it needs to see to formulate a plan.

> **Example Prompt:** "My goal is to migrate our project's authentication to use the `@supabase/ssr` library, following the server-side auth pattern in our design principles. I'm not sure which files are involved. Based on a standard Next.js application, what files or code snippets would you need to see to create a migration plan? Please list them out for me."

### Step 2: Provide the Requested Context
The AI will respond with a list of probable files (e.g., `middleware.ts`, `auth-provider.tsx`, `*.ts` files that create a supabase client, etc.). Your next step is to provide the content of those files.

> **Example Prompt:** "Great, thank you. Based on your questions, here is the current code for the files you identified as relevant:"
>
> `[Paste the code for middleware.ts]`
>
> `[Paste the code for the existing AuthProvider component]`
>
> `[Paste the code for any other relevant files]`

### Step 3: Request a Step-by-Step Plan (No Code Yet)
Now that the AI has the context, ask it to create a detailed plan *before* it generates any code. This forces it to "think" and allows you to review the proposed changes.

> **Example Prompt:** "Thank you for analyzing the files. Before you write the final code, please provide a detailed, step-by-step plan. For each file we discussed, tell me exactly what needs to be added, changed, or removed to complete the migration."

### Step 4: Execute the Plan Incrementally
Once you approve the plan, ask the AI to generate the code for each step, one at a time. This allows you to review, implement, and test each change in isolation.

> **Example Prompt:** "The plan looks solid. Let's start with step 1. Please provide the complete, updated code for the new `utils/supabase/server.ts` file."
>
> *(...after implementing...)*
>
> "Okay, that's done. Now, please provide the code for step 2: the new `middleware.ts` file."