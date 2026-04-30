import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

export default function ThemedSelect({
  value,
  onChange,
  options,
  placeholder,
  className = "",
  disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const [menuStyle, setMenuStyle] = useState({});
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);

  const selected = useMemo(
    () => options.find((option) => option.value === value),
    [options, value]
  );

  useEffect(() => {
    const handleOutsideClick = (event) => {
      const clickedTrigger = rootRef.current?.contains(event.target);
      const clickedMenu = menuRef.current?.contains(event.target);
      if (!clickedTrigger && !clickedMenu) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return;

    const updatePosition = () => {
      const rect = triggerRef.current.getBoundingClientRect();
      setMenuStyle({
        position: "fixed",
        top: rect.bottom - 1,
        left: rect.left,
        width: rect.width,
        zIndex: 9999,
      });
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open]);

  const handleSelect = (nextValue) => {
    onChange({ target: { value: nextValue } });
    setOpen(false);
  };

  return (
    <div
      ref={rootRef}
      className={`themed-select ${open ? "open" : ""} ${disabled ? "disabled" : ""} ${className}`.trim()}
    >
      <button
        type="button"
        ref={triggerRef}
        className="themed-select-trigger"
        onClick={() => !disabled && setOpen((prev) => !prev)}
        disabled={disabled}
      >
        <span className={`themed-select-value ${selected ? "" : "placeholder"}`.trim()}>
          {selected?.label || placeholder}
        </span>
        <span className="themed-select-chevron" aria-hidden="true">
          ▾
        </span>
      </button>

      {open &&
        createPortal(
          <div ref={menuRef} className="themed-select-menu" style={menuStyle}>
            {options.length > 0 ? (
              options.map((option) => (
                <button
                  key={option.value || option.label}
                  type="button"
                  className={`themed-select-option ${option.value === value ? "selected" : ""}`.trim()}
                  onClick={() => handleSelect(option.value)}
                >
                  {option.label}
                </button>
              ))
            ) : (
              <div className="themed-select-empty">No options available</div>
            )}
          </div>,
          document.body
        )}
    </div>
  );
}
