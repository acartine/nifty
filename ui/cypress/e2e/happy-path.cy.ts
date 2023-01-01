describe('happy path', () => {
  it('should create short url that successfully links to long url', () => {
    const longUrl = 'https://www.google.com/search?q=how+do+i+hit+long+shots+in+fifa+23'
    cy.visit('http://localhost/')
    cy.get('[data-testid="long-url-textfield"]').type(longUrl)
    cy.get('[data-testid="shorten-button"]').click()
    cy.get('[data-testid="copy-to-clipboard"]').click()
    cy.get('[data-testid="short-url-link"]').then((shortUrlLink) => {
      const shortUrl = shortUrlLink.text()
      cy.window().then(win => {
        win.navigator.clipboard.readText().then((text: string) => {
          expect(text).to.eq(shortUrl)
        })
      })
    })
    cy.get('[data-testid="short-url-link"]').invoke('removeAttr', 'target').click()

    cy.origin('https://www.google.com', { args: { longUrl } }, ({ longUrl }) => {
      cy.contains('how do i hit long shots in fifa 23')
      cy.url().should('include', longUrl)
    })
  })
})