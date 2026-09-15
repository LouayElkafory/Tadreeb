import { useEffect, type ReactNode } from 'react'

interface DrawerProps {
  open: boolean
  onClose: () => void
  side?: 'start' | 'end'
  children: ReactNode
}

export default function Drawer({ open, onClose, side = 'start', children }: DrawerProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  return (
    <div
      className={`fixed inset-0 z-50 lg:hidden ${open ? 'pointer-events-auto' : 'pointer-events-none'}`}
      aria-hidden={!open}
    >
      <div
        onClick={onClose}
        className={`absolute inset-0 bg-[var(--color-deep-navy)]/40 transition-opacity duration-300 ${
          open ? 'opacity-100' : 'opacity-0'
        }`}
      />
      <div
        className={`absolute top-0 h-full w-[84%] max-w-xs bg-white shadow-2xl transition-transform duration-300 ease-out ${
          side === 'start' ? 'start-0' : 'end-0'
        } ${open ? 'translate-x-0' : side === 'start' ? '-translate-x-full rtl:translate-x-full' : 'translate-x-full rtl:-translate-x-full'}`}
      >
        {children}
      </div>
    </div>
  )
}
