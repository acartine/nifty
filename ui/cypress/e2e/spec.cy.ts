import { cyan } from "@mui/material/colors"

describe('happy path', () => {
  it('should create short url that successfully links to long url', () => {
    const longUrl = 'https://www.google.com/search?q=how+do+i+hit+long+shots+in+fifa+23'
    cy.visit('http://localhost/')
    cy.contains('Long URL').type(longUrl)
    cy.contains('Shorten').click()
    cy.get('[data-testid="short-url-link"]').invoke('removeAttr', 'target').click()
    cy.origin('https://www.google.com', { args: { longUrl } }, ({ longUrl }) => {
      cy.contains('how do i hit long shots in fifa 23')
      cy.url().should('include', longUrl)
    })
  })
})