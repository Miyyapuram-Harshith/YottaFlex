# ERL-RMA Financial Settlement & Refund Mathematics

## 1. Principles
All monetary values in the ERL-RMA engine are stored and computed in integer cents or exact `Decimal` representation. Binary floating-point arithmetic (`IEEE 754 float`) is strictly prohibited.

Rounding uses Banker's Rounding (`ROUND_HALF_EVEN`) to minimize statistical bias over large volumes.

---

## 2. Invariant Properties

### Global Ledger Invariant
For any order line $k$, the cumulative net refund paid to the customer across all returns must never exceed the net amount paid at purchase plus any authorized shipping refunds:
$$\sum_{j} R_{\text{net}, j} \le \text{net\_paid\_amount} + \text{shipping\_refund\_amount}$$

Violation of this invariant is a critical financial leak (`ANOM_REFUND_EXCEEDS_PAID`) and is blocked at the database layer via SQLite triggers.

---

## 3. Cumulative Remainder Proration Formula

When an order line contains multiple units ($q_{\text{purchased}} > 1$) and is returned in fractional batches ($q_{\text{insp}} < q_{\text{purchased}}$), calculating proration line-by-line using independent rounding causes 1-cent penny drift:
$$\text{round}\left(\frac{\text{discount}}{q_{\text{purch}}} \times q_{\text{insp}}\right) \times n \ne \text{discount}$$

To prevent drift, the system computes cumulative shares using integer remainder allocation:

For the $k$-th unit or returned slice of quantity $q_k$:
$$\text{cum\_alloc}_k = \text{round\_half\_even}\left(\frac{\text{total\_amount} \times \sum_{i=1}^{k} q_i}{q_{\text{purchased}}}\right)$$
$$\text{slice\_amount}_k = \text{cum\_alloc}_k - \sum_{i=1}^{k-1} \text{slice\_amount}_i$$

This mathematical identity guarantees:
$$\sum_{k=1}^{M} \text{slice\_amount}_k \equiv \text{total\_amount}$$
Zero penny drift, regardless of whether returned in 2, 3, 7, or 10 separate portions.

---

## 4. Worked Step-by-Step Example

Consider an order line with 3 luxury jackets:
- Purchased Qty ($q_{\text{purchased}}$): `3`
- Inspected Return Qty ($q_{\text{insp}}$): `1`
- Unit Price: `$80.00` (`8,000` cents)
- Line Unit Total GMV: `$240.00` (`24,000` cents)
- Order Line Coupon Discount: `$15.00` (`1,500` cents)
- Order Line Tax Paid: `$18.00` (`1,800` cents)
- Total Net Paid for Line: `24,000 - 1,500 + 1,800 = 24,300` cents (`$243.00`)
- Item Grade: `GRADE_B_OPEN_BOX` (15% restocking fee)

### Step 1: Gross Merchandise Value (GMV)
$$\text{GMV}_{\text{slice}} = \text{unit\_price} \times q_{\text{insp}} = 8000 \times 1 = 8,000\text{ cents} \quad (\$80.00)$$

### Step 2: Cumulative Remainder Discount Clawback
- Total discount: `1,500` cents
- For slice 1 (qty 1 of 3):
  $$\text{cum}_1 = \text{round\_half\_even}\left(\frac{1500 \times 1}{3}\right) = 500\text{ cents} \quad (\$5.00)$$
- Discount clawed back: `$5.00` (`500` cents).

### Step 3: Net Merchandise Base
$$\text{Base} = \text{GMV}_{\text{slice}} - \text{Discount}_{\text{slice}} = 8,000 - 500 = 7,500\text{ cents} \quad (\$75.00)$$

### Step 4: Tax Refund
- Total tax: `1,800` cents
- For slice 1:
  $$\text{cum}_1 = \text{round\_half\_even}\left(\frac{1800 \times 1}{3}\right) = 600\text{ cents} \quad (\$6.00)$$
- Tax refunded: `$6.00` (`600` cents).

### Step 5: Restocking Fee Deduction
Condition `GRADE_B_OPEN_BOX` triggers 15% restocking fee on the base merchandise value:
$$\text{Restock} = \text{round\_half\_even}(7500 \times 0.15) = 1,125\text{ cents} \quad (\$11.25)$$

### Step 6: Shipping Refund
Customer reason `CHANGED_MIND` is customer-fault $\implies \$0.00$ shipping refund. (If reason was `DEFECTIVE` or `DAMAGED_IN_TRANSIT`, full order shipping fee of `$9.99` would be credited).

### Step 7: Final Net Refund
$$\text{Net Refund} = \text{Base} + \text{Tax} - \text{Restock} + \text{Shipping} = 7,500 + 600 - 1,125 + 0 = 6,975\text{ cents} \quad (\$69.75)$$

### Verification of Invariant
$$6,975 \le 24,300 \implies \mathbf{PASS}$$
When remaining 2 jackets are subsequently returned, slices receive `cum_2` and `cum_3`, exactly summing to the full `$243.00` without a single penny lost or gained.
