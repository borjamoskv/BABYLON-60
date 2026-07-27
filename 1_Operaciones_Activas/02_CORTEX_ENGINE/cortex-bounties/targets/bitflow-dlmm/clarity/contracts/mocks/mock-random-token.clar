;; Mock random Token
;; This token is NOT whitelisted in the system and is used for negative testing

(impl-trait .sip-010-trait-ft-standard-v-1-1.sip-010-trait)

;; Define the token
(define-fungible-token random-token)

;; Error constants
(define-constant ERR_NOT_AUTHORIZED (err u1))
(define-constant ERR_INVALID_AMOUNT (err u2))
(define-constant ERR_INVALID_PRINCIPAL (err u3))

;; Token metadata
(define-data-var token-name (string-ascii 32) "random Token")
(define-data-var token-symbol (string-ascii 32) "UNWL")
(define-data-var token-uri (optional (string-utf8 256)) (some u"https://random.token"))
(define-data-var token-decimals uint u6)

;; SIP-010 functions
(define-read-only (get-name)
  (ok (var-get token-name)))

(define-read-only (get-symbol)
  (ok (var-get token-symbol)))

(define-read-only (get-decimals)
  (ok (var-get token-decimals)))

(define-read-only (get-balance (user principal))
  (ok (ft-get-balance random-token user)))

(define-read-only (get-total-supply)
  (ok (ft-get-supply random-token)))

(define-read-only (get-token-uri)
  (ok (var-get token-uri)))

;; Transfer function
(define-public (transfer (amount uint) (sender principal) (recipient principal) (memo (optional (buff 34))))
  (begin
    (asserts! (is-eq sender tx-sender) ERR_NOT_AUTHORIZED)
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (asserts! (not (is-eq sender recipient)) ERR_INVALID_PRINCIPAL)
    (try! (ft-transfer? random-token amount sender recipient))
    (match memo to-print (print to-print) 0x)
    (ok true)))

;; Mint function - anyone can mint for testing
(define-public (mint (amount uint) (recipient principal))
  (begin
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (asserts! (is-standard recipient) ERR_INVALID_PRINCIPAL)
    (ft-mint? random-token amount recipient)))

;; Burn function
(define-public (burn (amount uint) (owner principal))
  (begin
    (asserts! (is-eq owner tx-sender) ERR_NOT_AUTHORIZED)
    (asserts! (> amount u0) ERR_INVALID_AMOUNT)
    (ft-burn? random-token amount owner)))