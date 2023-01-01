import { cyan } from "@mui/material/colors"

describe('idempotent', () => {
  it('should return the same short link if the same long link is shortened twice', () => {
    const longUrl = 'https://www.google.com/search?q=how+do+i+hit+long+shots+in+fifa+23'
    cy.visit('http://localhost/')
    cy.get('[data-testid="long-url-textfield"]').type(longUrl)
    cy.get('[data-testid="shorten-button"]').click()
    cy.get('[data-testid="short-url-link"]').then((shortUrlLink1) => {
      const shortLink1 = shortUrlLink1.text()
      cy.get('[data-testid="clear-button"]').click()
      cy.get('[data-testid="long-url-textfield"]').type('https://www.ea.com/games/fifa/fifa-23')
      cy.get('[data-testid="shorten-button"]').click()
      cy.get('[data-testid="clear-button"]').click()
      cy.get('[data-testid="long-url-textfield"]').type(longUrl)
      cy.get('[data-testid="shorten-button"]').click()
      cy.get('[data-testid="short-url-link"]').then((shortUrlLink2) => {
        const shortLink2 = shortUrlLink2.text()
        expect(shortLink1).to.eq(shortLink2)
      })
    })
  })
})
