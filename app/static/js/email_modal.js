class EmailModal {
    constructor(reportType) {
        this.reportType = reportType;
        this.emailContext = {
            type: null,
            year: null,
            month: null,
            filename: null,
            startDate: null,
            endDate: null,
            employeeSlug: null
        };
        this.adminUsers = [];
    }

    async loadAdminUsers() {
        try {
            const response = await fetch(`/reports/api/admin-users?report_type=${this.reportType}`);
            const result = await response.json();
            if (result.success) {
                this.adminUsers = result.users;
                this.renderUserList();
            }
        } catch (error) {
            console.error('Failed to load admin users:', error);
        }
    }

    renderUserList() {
        const container = document.getElementById('admin-users-list');
        if (!container) return;

        if (this.adminUsers.length === 0) {
            container.innerHTML = '<p style="color: #666; font-style: italic;">No admin users with emails found.</p>';
            return;
        }

        let html = '';
        this.adminUsers.forEach(user => {
            html += `
                <label class="user-checkbox-label">
                    <input type="checkbox"
                           name="user_email"
                           value="${user.email}"
                           data-user-id="${user.id}"
                           ${user.opt_in ? 'checked' : ''}>
                    <span>${user.username} (${user.email})</span>
                </label>
            `;
        });

        container.innerHTML = html;
    }

    openEmailModal(context) {
        this.emailContext = context;
        this.loadAdminUsers();

        const modal = document.getElementById('email-modal');
        modal.classList.add('active');
    }

    closeEmailModal() {
        const modal = document.getElementById('email-modal');
        modal.classList.remove('active');

        const checkboxes = document.querySelectorAll('input[name="user_email"]');
        checkboxes.forEach(cb => cb.checked = false);

        const additionalEmailField = document.getElementById('additional_email_input');
        if (additionalEmailField) additionalEmailField.value = '';

        const additionalEmailCheckbox = document.getElementById('additional_email_checkbox');
        if (additionalEmailCheckbox) additionalEmailCheckbox.checked = false;

        const additionalEmailContainer = document.getElementById('additional_email_container');
        if (additionalEmailContainer) additionalEmailContainer.style.display = 'none';

        this.emailContext = {
            type: null,
            year: null,
            month: null,
            filename: null,
            startDate: null,
            endDate: null,
            employeeSlug: null
        };
    }

    validateEmail(email) {
        const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return pattern.test(email);
    }

    async sendEmails(event) {
        event.preventDefault();

        const selectedEmails = [];
        const checkboxes = document.querySelectorAll('input[name="user_email"]:checked');
        checkboxes.forEach(cb => selectedEmails.push(cb.value));

        const additionalEmailCheckbox = document.getElementById('additional_email_checkbox');
        const additionalEmailInput = document.getElementById('additional_email_input');

        if (additionalEmailCheckbox && additionalEmailCheckbox.checked) {
            const additionalEmail = additionalEmailInput.value.trim();
            if (additionalEmail) {
                if (!this.validateEmail(additionalEmail)) {
                    alert('Please enter a valid email address');
                    return false;
                }
                selectedEmails.push(additionalEmail);
            }
        }

        if (selectedEmails.length === 0) {
            alert('Please select at least one recipient');
            return false;
        }

        let url;
        const formData = new FormData();

        selectedEmails.forEach(email => {
            formData.append('user_emails[]', email);
        });

        if (additionalEmailCheckbox && additionalEmailCheckbox.checked) {
            const additionalEmail = additionalEmailInput.value.trim();
            if (additionalEmail) {
                formData.append('additional_email', additionalEmail);
            }
        }

        const attachCsvCheckbox = document.getElementById('attach_csv_checkbox');
        if (attachCsvCheckbox && attachCsvCheckbox.checked) {
            formData.append('attach_csv', 'on');
        }

        if (this.emailContext.type === 'saved_daily') {
            url = `/reports/daily-balance/email/${this.emailContext.year}/${this.emailContext.month}/${this.emailContext.filename}`;
        } else if (this.emailContext.type === 'saved_tip') {
            url = `/reports/tip-report/email/${this.emailContext.filename}`;
        } else if (this.emailContext.type === 'export_daily') {
            url = '/reports/daily-balance/email';
            formData.append('start_date', this.emailContext.startDate);
            formData.append('end_date', this.emailContext.endDate);
        } else if (this.emailContext.type === 'export_tip') {
            url = '/reports/tip-report/email';
            formData.append('start_date', this.emailContext.startDate);
            formData.append('end_date', this.emailContext.endDate);
        } else if (this.emailContext.type === 'employee_tip') {
            url = `/reports/tip-report/employee/${this.emailContext.employeeSlug}/email`;
            formData.append('start_date', this.emailContext.startDate);
            formData.append('end_date', this.emailContext.endDate);
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                alert(result.message);
                this.closeEmailModal();
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (error) {
            alert(`Failed to send emails: ${error.message}`);
        }

        return false;
    }
}

function toggleAdditionalEmail() {
    const checkbox = document.getElementById('additional_email_checkbox');
    const container = document.getElementById('additional_email_container');
    if (checkbox.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
        document.getElementById('additional_email_input').value = '';
    }
}
