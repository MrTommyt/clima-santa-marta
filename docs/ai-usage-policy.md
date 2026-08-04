# AI usage policy

This project is a learning vehicle for data engineering, analysis, and ML. So that the
work remains honestly the author's, AI assistance is divided into three tiers. The rule
of thumb: **the author builds the data intelligence; AI builds or scaffolds the delivery
machinery.**

## AI encouraged

- Frontend scaffolding, CSS and responsive layouts, repetitive React components
- Docker and CI boilerplate
- Terraform module scaffolding
- Documentation formatting
- Test fixtures and mock API payloads
- Routine API serialization
- Accessibility review
- Debugging environment issues
- Code review after the author writes the implementation

## AI allowed with verification

- Terraform changes
- Database migrations
- Security configuration
- Kafka configuration
- Performance optimization
- Unit tests
- Dependency upgrades

Every AI-generated infrastructure change must pass, in order: format, validation, plan,
security scan, staging deployment, smoke tests.

## AI must not perform the core work

- Choosing analytical questions
- Defining transformations and data-cleaning decisions
- Exploratory analysis and interpreting visualizations
- Choosing statistical tests
- Designing target variables and feature engineering
- Preventing data leakage and selecting validation strategies
- Deciding which model is best
- Writing final analytical conclusions

AI may critique the author's completed work in these areas, but it must not silently
become the data scientist while the author supervises a progress bar.
