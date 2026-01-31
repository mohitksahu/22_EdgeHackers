import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GradientText from '../components/GradientText';
import "../styles/components/signup.css";

export default function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  const validatePasswords = (pwd, confirmPwd) => {
    if (confirmPwd && pwd !== confirmPwd) {
      setPasswordError('Passwords do not match');
    } else {
      setPasswordError('');
    }
  };

  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    validatePasswords(newPassword, confirmPassword);
  };

  const handleConfirmPasswordChange = (e) => {
    const newConfirmPassword = e.target.value;
    setConfirmPassword(newConfirmPassword);
    validatePasswords(password, newConfirmPassword);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }
    if (!termsAccepted) {
      // TODO: Show error message to user
      return;
    }
    setPasswordError('');
    // TODO: Implement actual signup logic
  };

  const handleGoogleSignup = () => {
    // TODO: Implement Google OAuth
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <h1>
            <GradientText>PLUTO<span>.</span></GradientText>
          </h1>
          <p className="login-tagline">Truth needs evidence</p>
        </div>

        {/* Signup Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <label>Full Name</label>
          <input
            type="text"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <label>Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={handlePasswordChange}
            required
            className={passwordError ? 'error' : ''}
          />

          <label>Confirm Password</label>
          <input
            type="password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={handleConfirmPasswordChange}
            required
            className={passwordError ? 'error' : ''}
          />
          {passwordError && <div className="error-message">{passwordError}</div>}

          {/* Terms and Conditions */}
          <div className="terms-checkbox">
            <input
              type="checkbox"
              id="terms"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              required
            />
            <label htmlFor="terms">
              I agree to the <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a> and <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
            </label>
          </div>

          <button type="submit" className="login-btn">
            Create Account
          </button>
        </form>

        {/* Sign In Button */}
        <button type="button" className="signup-btn" onClick={() => navigate('/login')}>
          Sign In
        </button>

        {/* Divider */}
        <div className="divider">
          <span>or continue with</span>
        </div>

        {/* OAuth Buttons */}
        <div className="oauth-section">
          <button className="oauth-btn google" type="button" onClick={handleGoogleSignup}>
            Continue with Google
          </button>
        </div>
      </div>
    </div>
  );
}