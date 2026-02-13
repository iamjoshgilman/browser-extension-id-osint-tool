import type { ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'
import styles from './AppShell.module.css'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <>
      <Header />
      <main className={styles.main}>{children}</main>
      <Footer />
    </>
  )
}
