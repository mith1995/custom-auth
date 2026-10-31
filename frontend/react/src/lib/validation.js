export const emailIsValid = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.trim());
export const passwordIsValid = (password) => password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password);

export function validateSignIn(values) {
  const errors = {};
  if (!emailIsValid(values.email)) errors.email = "Enter a valid email address.";
  if (!values.password) errors.password = "Enter your password.";
  return errors;
}

export function validateRegister(values) {
  const errors = {};
  if (values.name.trim().length < 2) errors.name = "Please enter your full name.";
  if (!emailIsValid(values.email)) errors.email = "Enter a valid email address.";
  if (!passwordIsValid(values.password)) errors.password = "Use 8+ characters with at least one letter and one number.";
  if (values.confirmPassword !== values.password) errors.confirmPassword = "Passwords do not match.";
  if (!values.acceptTerms) errors.acceptTerms = "Please accept the terms to continue.";
  return errors;
}

export function validateReset(values) {
  const errors = {};
  if (!passwordIsValid(values.password)) errors.password = "Use 8+ characters with at least one letter and one number.";
  if (values.confirmPassword !== values.password) errors.confirmPassword = "Passwords do not match.";
  return errors;
}
