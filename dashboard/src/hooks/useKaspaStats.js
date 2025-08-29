import { useEffect, useState } from 'react'

export function useKaspaStats() {
  const [price, setPrice] = useState(0.0567)
  const [change24h, setChange24h] = useState(2.34)
  const [updatedAt, setUpdatedAt] = useState(Date.now())

  useEffect(() => {
    const id = setInterval(() => {
      setPrice(p => Math.max(0, p + (Math.random() - 0.5) * 0.002))
      setChange24h(c => Math.max(-20, Math.min(20, c + (Math.random() - 0.5) * 0.2)))
      setUpdatedAt(Date.now())
    }, 2500)
    return () => clearInterval(id)
  }, [])

  return { price, change24h, updatedAt }
}
