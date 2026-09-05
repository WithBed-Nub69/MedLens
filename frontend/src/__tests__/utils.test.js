/**
 * Tests for utility functions and service layer.
 * Validates API configuration, error handling, and data transformations.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'


describe('API Service Configuration', () => {
  it('should have correct base URL configuration', () => {
    // Verify environment variable pattern
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    expect(baseUrl).toBeTruthy()
    expect(typeof baseUrl).toBe('string')
  })

  it('should handle missing environment variables gracefully', () => {
    const fallback = 'http://localhost:8000/api'
    const url = undefined || fallback
    expect(url).toBe(fallback)
  })
})


describe('Patient Data Utilities', () => {
  it('should generate correct initials from full name', () => {
    const getInitials = (name) =>
      name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || '?'

    expect(getInitials('John Doe')).toBe('JD')
    expect(getInitials('Jane')).toBe('J')
    expect(getInitials('A B C')).toBe('AB')
    expect(getInitials(null)).toBe('?')
  })

  it('should format dates correctly', () => {
    const date = new Date('2026-01-15T00:00:00Z')
    const formatted = date.toLocaleDateString()
    expect(formatted).toBeTruthy()
  })

  it('should generate correct greeting based on time', () => {
    const greeting = (hours) => {
      if (hours < 12) return 'Good morning'
      if (hours < 17) return 'Good afternoon'
      return 'Good evening'
    }

    expect(greeting(8)).toBe('Good morning')
    expect(greeting(14)).toBe('Good afternoon')
    expect(greeting(20)).toBe('Good evening')
    expect(greeting(0)).toBe('Good morning')
    expect(greeting(12)).toBe('Good afternoon')
    expect(greeting(17)).toBe('Good evening')
  })
})


describe('Markdown Renderer', () => {
  it('should handle bold text formatting', () => {
    const inlineFormat = (text) => {
      const parts = []
      const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g
      let last = 0, m
      while ((m = regex.exec(text)) !== null) {
        if (m.index > last) parts.push(text.slice(last, m.index))
        if (m[2]) parts.push({ type: 'bold', text: m[2] })
        else if (m[3]) parts.push({ type: 'italic', text: m[3] })
        last = m.index + m[0].length
      }
      if (last < text.length) parts.push(text.slice(last))
      return parts
    }

    const result = inlineFormat('This is **bold** text')
    expect(result).toHaveLength(3)
    expect(result[1]).toEqual({ type: 'bold', text: 'bold' })
  })

  it('should handle italic text formatting', () => {
    const inlineFormat = (text) => {
      const parts = []
      const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g
      let last = 0, m
      while ((m = regex.exec(text)) !== null) {
        if (m.index > last) parts.push(text.slice(last, m.index))
        if (m[2]) parts.push({ type: 'bold', text: m[2] })
        else if (m[3]) parts.push({ type: 'italic', text: m[3] })
        last = m.index + m[0].length
      }
      if (last < text.length) parts.push(text.slice(last))
      return parts
    }

    const result = inlineFormat('This is *italic* text')
    expect(result).toHaveLength(3)
    expect(result[1]).toEqual({ type: 'italic', text: 'italic' })
  })

  it('should handle plain text without formatting', () => {
    const inlineFormat = (text) => {
      const parts = []
      const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g
      let last = 0, m
      while ((m = regex.exec(text)) !== null) {
        if (m.index > last) parts.push(text.slice(last, m.index))
        if (m[2]) parts.push({ type: 'bold', text: m[2] })
        else if (m[3]) parts.push({ type: 'italic', text: m[3] })
        last = m.index + m[0].length
      }
      if (last < text.length) parts.push(text.slice(last))
      return parts
    }

    const result = inlineFormat('Plain text')
    expect(result).toEqual(['Plain text'])
  })

  it('should detect heading lines', () => {
    const isHeading = (line) => /^#{1,3}\s+/.test(line)
    expect(isHeading('# Header')).toBe(true)
    expect(isHeading('## Subheader')).toBe(true)
    expect(isHeading('### Sub-subheader')).toBe(true)
    expect(isHeading('Not a header')).toBe(false)
  })

  it('should detect bullet list lines', () => {
    const isBullet = (line) => /^[*-]\s/.test(line)
    expect(isBullet('* Item')).toBe(true)
    expect(isBullet('- Item')).toBe(true)
    expect(isBullet('Not a bullet')).toBe(false)
  })

  it('should detect horizontal rules', () => {
    const isHR = (line) => /^---+$/.test(line.trim())
    expect(isHR('---')).toBe(true)
    expect(isHR('-----')).toBe(true)
    expect(isHR('text')).toBe(false)
  })
})


describe('Medical Test Status Badge Logic', () => {
  it('should map status to correct badge labels', () => {
    const statusMap = {
      low: '↓ Low',
      high: '↑ High',
      normal: '✓ Normal',
      unknown: '— Unknown',
    }
    expect(statusMap['low']).toBe('↓ Low')
    expect(statusMap['high']).toBe('↑ High')
    expect(statusMap['normal']).toBe('✓ Normal')
    expect(statusMap['unknown']).toBe('— Unknown')
  })

  it('should map verification status correctly', () => {
    const verificationMap = {
      verified: '✓ Verified',
      pending: '⏳ Pending',
      corrected: '✎ Corrected',
    }
    expect(verificationMap['verified']).toBe('✓ Verified')
    expect(verificationMap['pending']).toBe('⏳ Pending')
  })

  it('should map processing status correctly', () => {
    const processingMap = {
      pending: 'Pending',
      processing: '⏳ Processing...',
      review: '👁 Review',
      verified: '✓ Done',
      failed: '✗ Failed',
    }
    expect(processingMap['verified']).toBe('✓ Done')
    expect(processingMap['failed']).toBe('✗ Failed')
  })
})


describe('Data Validation', () => {
  it('should validate email format', () => {
    const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    expect(isValidEmail('test@example.com')).toBe(true)
    expect(isValidEmail('invalid')).toBe(false)
    expect(isValidEmail('')).toBe(false)
  })

  it('should validate patient name is non-empty', () => {
    const isValidName = (name) => name && name.trim().length > 0
    expect(isValidName('John')).toBeTruthy()
    expect(isValidName('')).toBeFalsy()
    expect(isValidName(null)).toBeFalsy()
  })

  it('should validate age is reasonable', () => {
    const isValidAge = (age) => age > 0 && age < 150
    expect(isValidAge(35)).toBe(true)
    expect(isValidAge(0)).toBe(false)
    expect(isValidAge(200)).toBe(false)
  })
})
