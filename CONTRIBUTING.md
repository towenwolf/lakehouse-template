# Contributing to Lakehouse Template

Thank you for your interest in contributing to the Lakehouse Template! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists in the [Issues](https://github.com/towenwolf/lakehouse-template/issues) section
2. If not, create a new issue with a clear title and description
3. Include relevant details:
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Environment details (OS, tool versions, etc.)
   - Screenshots or logs if applicable

### Suggesting Enhancements

We welcome suggestions for new features or improvements:

1. Open an issue with the label "enhancement"
2. Describe the feature and its benefits
3. Provide use cases or examples
4. Discuss implementation approaches if you have ideas

### Contributing Code

#### Before You Start

1. Check existing issues and pull requests to avoid duplicates
2. For major changes, open an issue first to discuss the approach
3. Fork the repository and create a branch from `main`
4. Follow the existing code style and structure

#### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/lakehouse-template.git
cd lakehouse-template

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Test your changes
# (add testing steps specific to your contribution)
```

#### Making Changes

**For Configuration Templates:**
1. Add the configuration file(s) to the appropriate directory
2. Include comments explaining each configuration option
3. Provide default values that work out of the box
4. Create a README.md in the tool's directory with:
   - Installation instructions
   - Configuration explanations
   - Usage examples
   - Troubleshooting tips

**For Example Pipelines:**
1. Add the pipeline to `pipelines/examples/`
2. Include comprehensive comments
3. Use logging and monitoring patterns from existing examples
4. Handle errors gracefully
5. Document any dependencies

**For Documentation:**
1. Use clear, concise language
2. Include code examples
3. Add visual diagrams where helpful
4. Keep formatting consistent with existing docs
5. Update the table of contents if needed

#### Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "Add Trino configuration template"
git commit -m "Fix Spark logging configuration for Python 3.11"
git commit -m "Update ARCHITECTURE.md with security best practices"

# Bad commit messages
git commit -m "Update files"
git commit -m "Fix bug"
git commit -m "WIP"
```

Format:
- Use present tense ("Add feature" not "Added feature")
- Start with a capital letter
- Keep the first line under 50 characters
- Add detailed description in the body if needed

#### Pull Request Process

1. **Update Documentation**
   - Update README.md if adding new features
   - Add/update relevant docs in `docs/`
   - Include inline comments for complex code

2. **Test Your Changes**
   - Verify configuration files are valid
   - Test example pipelines work as expected
   - Check documentation renders correctly

3. **Create Pull Request**
   - Use a clear, descriptive title
   - Fill out the PR template (if provided)
   - Reference any related issues
   - Explain what changed and why
   - Add screenshots for UI/visual changes

4. **Code Review**
   - Respond to feedback promptly
   - Make requested changes
   - Keep the discussion professional and constructive

5. **Merge**
   - Maintainers will merge once approved
   - Your contribution will be credited

## What We're Looking For

### High Priority

- [ ] Additional tool configurations (Trino, Flink, etc.)
- [ ] More example pipelines (real-world scenarios)
- [ ] Data quality framework examples
- [ ] CI/CD pipeline templates
- [ ] Infrastructure as Code examples (Terraform, CloudFormation)
- [ ] Security best practices documentation
- [ ] Performance optimization guides

### Medium Priority

- [ ] Additional monitoring integrations (Datadog, New Relic, etc.)
- [ ] Testing framework examples
- [ ] Data governance patterns
- [ ] Cost optimization strategies
- [ ] Disaster recovery procedures
- [ ] Multi-region deployment patterns

### Nice to Have

- [ ] Video tutorials
- [ ] Interactive demos
- [ ] Case studies
- [ ] Migration guides from other architectures
- [ ] Troubleshooting guides
- [ ] FAQ section

## Contribution Types

### 1. Tool Configurations

Add support for a new tool:

```
config/tools/[tool-name]/
├── README.md              # Required
├── [tool-config-file]     # Tool's config
└── example-usage.md       # Optional
```

### 2. Example Pipelines

Add a new example pipeline:

```
pipelines/examples/
├── [tool]_[use-case].py   # Main pipeline
├── README.md              # Explanation
└── sample_data/           # Optional test data
```

### 3. Documentation

Improve or add documentation:

```
docs/
├── [TOPIC].md             # New documentation
└── assets/                # Images, diagrams
    └── [diagram].png
```

### 4. Configuration Examples

Add environment-specific configs:

```
config/environments/
├── development/
├── staging/
└── production/
```

## Style Guidelines

### Code Style

- **Python**: Follow PEP 8
  - Use 4 spaces for indentation
  - Maximum line length: 100 characters
  - Use type hints where applicable

- **SQL**: Follow consistent formatting
  - Keywords in UPPERCASE
  - Indentation for readability
  - Meaningful aliases

- **YAML**: Follow consistent formatting
  - Use 2 spaces for indentation
  - Keep alphabetical order where logical
  - Include comments for complex sections

### Documentation Style

- Use Markdown for all documentation
- Include code blocks with language specification
- Use tables for comparisons
- Add visual diagrams for complex concepts
- Link to external resources when relevant
- Keep paragraphs concise

### Configuration Style

- Include comprehensive comments
- Provide sensible defaults
- Group related settings together
- Add links to official documentation
- Note any version-specific configurations

## Testing

While this is a template project, please ensure:

1. **Configuration Validity**
   - Configurations parse correctly
   - No syntax errors

2. **Example Functionality**
   - Example pipelines run successfully
   - Dependencies are documented
   - Output is as expected

3. **Documentation Accuracy**
   - Links work correctly
   - Code examples run without errors
   - Instructions are complete

## Community Guidelines

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the contribution, not the contributor
- Assume good intentions
- Ask questions instead of making assumptions

## Recognition

Contributors will be:
- Listed in the repository contributors
- Mentioned in release notes for significant contributions
- Credited in documentation where appropriate

## Questions?

- Open an issue for general questions
- Tag maintainers for urgent matters
- Join discussions in existing issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for making the Lakehouse Template better! 🎉
