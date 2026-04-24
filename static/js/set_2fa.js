document.addEventListener('DOMContentLoaded', function () {
	const enable2FA = document.getElementById('enable2FA');
	const modalEl = document.getElementById('twoFAModal');
	const verifyBtn = document.getElementById('verify2FA');
	const cancelBtn = document.getElementById('cancel2FA');
	const otpError = document.getElementById('otpError');
	const otpDigits = document.querySelectorAll('.otp-digit');
	const qrImage = document.querySelector('#twoFAModal .qr-placeholder img');
	const twoFAStatus = document.getElementById('twoFAStatus');

	if (!enable2FA || !modalEl || !verifyBtn || otpDigits.length === 0) {
		return;
	}

	window.__set2faManaged = true;

	const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
	let isVerified = false;
	let isLoadingQr = false;

	function clearOtpInputs() {
		otpDigits.forEach((el) => {
			el.value = '';
		});
	}

	function setError(message) {
		if (!otpError) {
			return;
		}

		otpError.textContent = message;
		otpError.style.display = 'block';
	}

	function clearError() {
		if (!otpError) {
			return;
		}

		otpError.style.display = 'none';
	}

	function setVerifyBtnLoading(isLoading) {
		verifyBtn.disabled = isLoading;

		if (isLoading) {
			verifyBtn.dataset.originalHtml = verifyBtn.innerHTML;
			verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Ellenorzes...';
		} else if (verifyBtn.dataset.originalHtml) {
			verifyBtn.innerHTML = verifyBtn.dataset.originalHtml;
		}
	}

	function bindOtpInputs() {
		otpDigits.forEach((input, index) => {
			input.addEventListener('input', function () {
				this.value = this.value.replace(/[^0-9]/g, '');

				if (this.value.length === 1 && index < otpDigits.length - 1) {
					otpDigits[index + 1].focus();
				}
			});

			input.addEventListener('keydown', function (event) {
				if (event.key === 'Backspace' && this.value === '' && index > 0) {
					otpDigits[index - 1].focus();
				}
			});

			input.addEventListener('paste', function (event) {
				event.preventDefault();
				const pastedText = (event.clipboardData || window.clipboardData).getData('text');
				const digits = pastedText.replace(/[^0-9]/g, '').slice(0, otpDigits.length);

				digits.split('').forEach((digit, idx) => {
					if (otpDigits[idx]) {
						otpDigits[idx].value = digit;
					}
				});

				const nextIndex = Math.min(digits.length, otpDigits.length - 1);
				otpDigits[nextIndex].focus();
			});
		});
	}

	async function requestQrCode() {
		if (isLoadingQr) {
			return;
		}

		isLoadingQr = true;
		clearError();

		try {
			const response = await fetch('/create2fa', {
				method: 'POST',
				headers: {
					'X-Requested-With': 'XMLHttpRequest'
				}
			});

			const data = await response.json();

			if (!response.ok || !data.success) {
				throw new Error(data.error || 'Nem sikerult a 2FA inicializalasa.');
			}

			if (data.qr_code && qrImage) {
				qrImage.src = `data:image/png;base64,${data.qr_code}`;
			}
		} catch (error) {
			enable2FA.checked = false;
			setError(error.message || 'Nem sikerult betolteni a QR kodot.');
			throw error;
		} finally {
			isLoadingQr = false;
		}
	}

	async function verifyOtpCode(code) {
		const formData = new FormData();
		formData.append('2fa_code', code);

		const response = await fetch('/create2fa', {
			method: 'POST',
			body: formData,
			headers: {
				'X-Requested-With': 'XMLHttpRequest'
			}
		});

		const data = await response.json();

		if (!response.ok || !data.success) {
			throw new Error(data.error || 'Hibas kod, kerlek probald ujra.');
		}

		return data;
	}

	function updateTwoFAStatus(enabled) {
		if (twoFAStatus) {
			if (enabled) {
				twoFAStatus.textContent = 'Bekapcsolva';
				twoFAStatus.setAttribute('data-i18n', 'profile.enabled');
				if (enable2FA.parentElement) {
					const icon = enable2FA.parentElement.querySelector('i');
					if (icon) {
						icon.className = 'fas fa-lock';
					}
				}
			} else {
				twoFAStatus.textContent = 'Kikapcsolva';
				twoFAStatus.setAttribute('data-i18n', 'profile.disabled');
				if (enable2FA.parentElement) {
					const icon = enable2FA.parentElement.querySelector('i');
					if (icon) {
						icon.className = 'fas fa-lock-open';
					}
				}
			}
		}
	}

	enable2FA.addEventListener('change', async function () {
		const isCurrentlyEnabled = enable2FA.dataset['2faEnabled'] === 'true';

		if (isCurrentlyEnabled && !this.checked) {
			isVerified = false;
			verifyBtn.dataset.verified = '';
			enable2FA.dataset['2faEnabled'] = 'false';
			updateTwoFAStatus(false);
			clearOtpInputs();
			clearError();
			return;
		}

		if (!isCurrentlyEnabled && this.checked) {
			clearOtpInputs();
			modal.show();

			try {
				await requestQrCode();
			} catch {
				modal.hide();
			}
			return;
		}

		if (!this.checked) {
			isVerified = false;
			verifyBtn.dataset.verified = '';
			clearOtpInputs();
			clearError();
			return;
		}
	});

	verifyBtn.addEventListener('click', async function (event) {
		event.preventDefault();
		event.stopImmediatePropagation();

		const code = Array.from(otpDigits).map((digit) => digit.value).join('');

		if (!/^\d{6}$/.test(code)) {
			setError('Kerlek add meg mind a 6 szamjegyet!');
			return;
		}

		setVerifyBtnLoading(true);
		clearError();

		try {
			await verifyOtpCode(code);
			isVerified = true;
			verifyBtn.dataset.verified = 'true';
			enable2FA.dataset['2faEnabled'] = 'true';
			updateTwoFAStatus(true);
			modal.hide();

			if (typeof showToast === 'function') {
				showToast('Ketlepcsos azonositas sikeresen bekapcsolva!', 'success');
			}
		} catch (error) {
			isVerified = false;
			verifyBtn.dataset.verified = '';
			setError(error.message || 'Hibas kod, kerlek probald ujra.');
			clearOtpInputs();
			otpDigits[0].focus();
		} finally {
			setVerifyBtnLoading(false);
		}
	}, true);

	if (cancelBtn) {
		cancelBtn.addEventListener('click', function () {
			if (!isVerified) {
				enable2FA.checked = false;
			}

			clearOtpInputs();
			clearError();
			modal.hide();
		});
	}

	modalEl.addEventListener('hidden.bs.modal', function () {
		if (!isVerified) {
			enable2FA.checked = false;
			verifyBtn.dataset.verified = '';
		}

		clearOtpInputs();
		clearError();
	});

	bindOtpInputs();
});

