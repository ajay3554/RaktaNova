const PERSON_NAME_PATTERN = /^[A-Za-z]+(?: [A-Za-z]+)*$/;
const INDIAN_MOBILE_PATTERN = /^[6-9]\d{9}$/;

const NAME_ERROR = "Name can contain letters and spaces only.";
const MOBILE_ERROR = "Enter a valid 10-digit Indian mobile number.";
const AGE_ERROR = "Age must be between 18 and 60.";
const DUPLICATE_MOBILE_ERROR = "This mobile number is already registered.";


function getApiDetail(data) {
    const detail = data && data.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail) && detail[0] && typeof detail[0].msg === "string") {
        return detail[0].msg.replace(/^Value error,\s*/i, "");
    }

    return "";
}


function fieldErrorElement(input) {
    if (!input || !input.id) {
        return null;
    }

    return document.getElementById(input.id + "-error");
}


function setFieldError(input, message) {
    if (!input) {
        return;
    }

    const errorEl = fieldErrorElement(input);

    input.classList.add("input-invalid");
    input.setAttribute("aria-invalid", "true");

    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add("is-visible");
    }
}


function clearFieldError(input) {
    if (!input) {
        return;
    }

    const errorEl = fieldErrorElement(input);

    input.classList.remove("input-invalid");
    input.removeAttribute("aria-invalid");

    if (errorEl) {
        errorEl.textContent = "";
        errorEl.classList.remove("is-visible");
    }
}


function validatePersonName(value) {
    const name = String(value || "").trim();

    if (!PERSON_NAME_PATTERN.test(name)) {
        return { ok: false, value: name, message: NAME_ERROR };
    }

    return { ok: true, value: name };
}


function validateIndianMobile(value) {
    const phone = String(value || "").trim();

    if (!INDIAN_MOBILE_PATTERN.test(phone)) {
        return { ok: false, value: phone, message: MOBILE_ERROR };
    }

    return { ok: true, value: phone };
}


function validateDonorAge(value) {
    const raw = value == null ? "" : String(value).trim();

    if (!/^[0-9]+$/.test(raw)) {
        return { ok: false, value: raw, message: AGE_ERROR };
    }

    const age = Number(raw);

    if (!Number.isInteger(age) || age < 18 || age > 60) {
        return { ok: false, value: raw, message: AGE_ERROR };
    }

    return { ok: true, value: age };
}


function attachPersonNameField(input) {
    if (!input) {
        return;
    }

    const check = function (showWhenEmpty) {
        const result = validatePersonName(input.value);

        if (result.ok) {
            clearFieldError(input);
            return true;
        }

        if (!String(input.value || "").trim() && !showWhenEmpty) {
            clearFieldError(input);
            return false;
        }

        setFieldError(input, result.message);
        return false;
    };

    input.addEventListener("input", function () {
        check(false);
    });

    input.addEventListener("blur", function () {
        check(Boolean(input.value));
    });
}


function attachIndianMobileField(input) {
    if (!input) {
        return;
    }

    input.setAttribute("inputmode", "numeric");
    input.setAttribute("autocomplete", "tel");

    input.addEventListener("keydown", function (event) {
        if (event.ctrlKey || event.metaKey || event.altKey) {
            return;
        }

        const navigationKeys = [
            "Backspace",
            "Tab",
            "ArrowLeft",
            "ArrowRight",
            "Delete",
            "Home",
            "End",
            "Enter"
        ];

        if (navigationKeys.includes(event.key)) {
            return;
        }

        if (!/^\d$/.test(event.key)) {
            event.preventDefault();
            setFieldError(input, MOBILE_ERROR);
            return;
        }

        const selected = (input.selectionEnd || 0) - (input.selectionStart || 0);

        if (input.value.length - selected >= 10) {
            event.preventDefault();
            setFieldError(input, MOBILE_ERROR);
        }
    });

    input.addEventListener("paste", function (event) {
        const text = ((event.clipboardData && event.clipboardData.getData("text")) || "").trim();

        event.preventDefault();
        input.value = text;

        const result = validateIndianMobile(text);

        if (result.ok) {
            clearFieldError(input);
        } else {
            setFieldError(input, result.message);
        }
    });

    input.addEventListener("input", function () {
        if (!input.value) {
            clearFieldError(input);
            return;
        }

        const result = validateIndianMobile(input.value);

        if (result.ok) {
            clearFieldError(input);
        } else {
            setFieldError(input, result.message);
        }
    });

    input.addEventListener("blur", function () {
        if (!input.value) {
            return;
        }

        const result = validateIndianMobile(input.value);

        if (!result.ok) {
            setFieldError(input, result.message);
        }
    });
}


function attachDonorAgeField(input) {
    if (!input) {
        return;
    }

    input.setAttribute("min", "18");
    input.setAttribute("max", "60");
    input.setAttribute("step", "1");
    input.setAttribute("inputmode", "numeric");

    input.addEventListener("invalid", function (event) {
        event.preventDefault();
        setFieldError(input, AGE_ERROR);
    });

    input.addEventListener("input", function () {
        if (!input.value) {
            clearFieldError(input);
            return;
        }

        const result = validateDonorAge(input.value);

        if (result.ok) {
            clearFieldError(input);
        } else {
            setFieldError(input, result.message);
        }
    });

    input.addEventListener("blur", function () {
        if (!input.value) {
            return;
        }

        const result = validateDonorAge(input.value);

        if (!result.ok) {
            setFieldError(input, result.message);
        }
    });
}


document.addEventListener("DOMContentLoaded", function () {
    attachPersonNameField(document.getElementById("donor-name"));
    attachDonorAgeField(document.getElementById("donor-age"));
    attachIndianMobileField(document.getElementById("donor-phone"));
    attachIndianMobileField(document.getElementById("donor-login-phone"));
    attachIndianMobileField(document.getElementById("login-phone"));
});
