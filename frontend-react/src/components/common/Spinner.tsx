import styles from './Spinner.module.css'

interface SpinnerProps {
  message?: string
}

export function Spinner({ message }: SpinnerProps) {
  return (
    <div className={styles.container}>
      <div className={styles.spinner} />
      {message && <p className={styles.message}>{message}</p>}
    </div>
  )
}
