import React, { useState, useEffect } from 'react';

const Dialog = ({ children, open, onOpenChange }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {/* Dialog content will be rendered by children */}
      {children}
    </div>
  );
};

const DialogContent = ({ children, className = '' }) => (
  <div className={`relative bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] rounded-xl shadow-2xl max-w-lg w-full mx-4 ${className}`}>
    {children}
  </div>
);

const DialogHeader = ({ children }) => (
  <div className="px-8 py-6 border-b border-[var(--card-border,#1f1f2e)]">
    {children}
  </div>
);

const DialogTitle = ({ children, className = '' }) => (
  <h2 className={`text-lg font-semibold text-[var(--text-color)] ${className}`}>
    {children}
  </h2>
);

const DialogDescription = ({ children, className = '' }) => (
  <p className={`text-sm text-[var(--text-secondary,#8b8b9f)] mt-2 ${className}`}>
    {children}
  </p>
);

const DialogTrigger = ({ children, asChild, ...props }) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, props);
  }
  return <button {...props}>{children}</button>;
};

const DialogClose = ({ children, asChild, onClick, ...props }) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, { onClick, ...props });
  }
  return (
    <button
      onClick={onClick}
      className="absolute top-6 right-6 text-[var(--text-secondary,#8b8b9f)] hover:text-[var(--text-color)] transition-colors w-6 h-6 flex items-center justify-center rounded-full hover:bg-[var(--card-border,#1f1f2e)]/50"
      {...props}
    >
      ✕
    </button>
  );
};

export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
  DialogClose,
};