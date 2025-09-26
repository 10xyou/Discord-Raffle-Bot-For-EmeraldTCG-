# 🎟️ Discord Raffle Bot for EmeraldTCG

I built this bot for the Biggest Pokémon Discord server in Ireland (1000+ members), and it’s used daily! Users can start raffles, join spots, and track payments. It makes managing raffkes easy and interactive for the community. ⚡

---

## Features

### 1. **Start a Raffle** 🏁
- Command: `!start` (Trusted Seller role required)
- Starts a new raffle in the current channel.
- The bot prompts for:
  1. 🎁 What is being raffled
  2. 🔢 Number of spots available
  3. 💶 Price per spot
  4. 💳 Payment method (Revolut or PayPal)
- Creates a visual list of spots for users to claim.

### 2. **Join Spots** ✋
- Command: `!spots <spot numbers>`
- Users can claim unclaimed spots by specifying the spot numbers.
- Already taken spots trigger a notification.
- Automatically updates the raffle display.

### 3. **Mini Spots** 🪙
- Command: `!mini <spot numbers>` or `!minirandoms <number>`
- Lets users claim spots as “Mini” (special secondary spots).
- Random or manual spot claiming is supported.

### 4. **Random Spot Assignment** 🎲
- Command: `!randoms <number>`
- Assigns a specified number of random unclaimed spots to the user.

### 5. **Remove a Spot** ❌
- Command: `!remove <spot numbers>`
- Allows a user to remove their own claimed spots.
- Updates the raffle display automatically.

### 6. **Mark as Paid** 💰
- Command: `!paid`
- Users mark their spots as paid.
- Mini and regular spots tracked separately.
- Bot notifies when all spots are paid.

### 7. **Check Payment Status** 📊
- Command: `!payment` (Trusted Seller role required)
- Displays users who haven’t paid yet, with amount due and payment method.

### 8. **Pause/Unpause Raffle** ⏸️▶️
- Commands: `!pause`, `!unpause`
- Trusted Sellers can pause the main raffle to prevent further claims.

### 9. **Check Remaining Spots** 🔢
- Command: `!remaining`
- Shows all unclaimed spots in the current raffle.

### 10. **Check Your Spots** 📩
- Command: `!myspots`
- Sends a DM to the user with all spots they own (regular and mini).

### 11. **Raffle Link** 🔗
- Command: `!razz`
- Provides a direct link to the current raffle message in the channel.

### 12. **Check Payment Info** 💳
- Command: `!rev`
- Displays the payment method for the current raffle (Revolut or PayPal).

---

## How It Works ⚙️
1. Trusted Sellers start a raffle using `!start`.
2. Users claim spots with `!spots` or `!mini` or `!randoms` or `!minirandoms`.
3. Users can remove spots in raffle using `!remove`
4. Users mark spots as paid using `!paid`.
5. Trusted Sellers can check who has not paid with `!payment`.
6. Raffles can be paused or unpaused with `!pause`/`!unpause`.
7. Users can get the hosts revolut by doing `!rev`.
8. Users can check their spots in the raffle by doing `!myspots` which will dm them their spots.
9. Users can check how many spots left in the raffle by doing `!remaining`
10. Users can see the raffle happening currently by doing `!razz`
11. The bot automatically updates the list of spots in the channel.
