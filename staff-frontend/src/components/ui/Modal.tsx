"use client";

import React, { useEffect } from "react";
import { Dialog } from "@headlessui/react";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";
import { ModalProps } from "@/types";
import Button from "./Button";

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  className,
}) => {
  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
  };

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        aria-hidden="true"
      />

      {/* Full-screen container */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel
          className={cn(
            "w-full bg-dark-800 border border-dark-600 rounded-2xl shadow-2xl overflow-hidden",
            sizeClasses[size],
            className,
          )}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between p-6 border-b border-dark-600">
              <Dialog.Title className="text-xl font-semibold text-white">
                {title}
              </Dialog.Title>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-dark-700"
              >
                <XMarkIcon className="w-5 h-5" />
              </Button>
            </div>
          )}

          {/* Content */}
          <div className="p-6">{children}</div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default Modal;
