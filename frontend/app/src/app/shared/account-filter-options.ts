export const ALL_ACCOUNTS_LABEL = 'All Accounts';
export const ALL_ACCOUNTS_VALUE = '__all_accounts__';

export interface AccountFilterOption {
  value: string;
  label: string;
  accountNames: string[];
}

export function createAccountFilterOptions(accountNames: string[]): AccountFilterOption[] {
  const groups = new Map<string, AccountFilterOption>();
  let unnamedAccountCount = 0;

  for (const rawName of accountNames) {
    const accountName = rawName.trim();
    if (!accountName || accountName.toLowerCase() === ALL_ACCOUNTS_LABEL.toLowerCase()) continue;

    const accountNumber = extractAccountNumber(accountName);
    const key = accountNumber
      ? `number:${accountNumber}`
      : `name:${normalizeAccountName(accountName)}`;
    let option = groups.get(key);

    if (!option) {
      option = {
        value: `account-${groups.size}`,
        label: accountNumber ? `•••• ${accountNumber.slice(-4)}` : `Account ${++unnamedAccountCount}`,
        accountNames: []
      };
      groups.set(key, option);
    }

    if (!option.accountNames.includes(accountName)) {
      option.accountNames.push(accountName);
    }
  }

  return [...groups.values()];
}

function normalizeAccountName(accountName: string): string {
  const normalizedName = accountName
    .replace(/[_\s-]+(?:19|20)\d{2}(?=$|[_\s-])/g, ' ')
    .replace(/[_\s-]+(?:mod|modified)(?=$|[_\s-])/gi, ' ')
    .replace(/[_\s-]+/g, ' ')
    .trim()
    .toLowerCase();

  return normalizedName || accountName.toLowerCase();
}

function extractAccountNumber(accountName: string): string | null {
  const maskedAccount = accountName.match(/x{2,}(\d+)/i);
  if (maskedAccount) return maskedAccount[1];

  const numericIdentifiers = accountName.match(/\d{9,}/g);
  return numericIdentifiers?.sort((left, right) => right.length - left.length)[0] ?? null;
}
