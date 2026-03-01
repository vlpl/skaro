/**
 * Compute unified diff lines between old and new content.
 * Returns array of { type: 'ctx'|'add'|'del'|'sep', oldNum, newNum, text }
 */
export function computeUnifiedDiff(oldContent, newContent, isNew) {
	if (isNew || oldContent == null) {
		return newContent.split('\n').map((line, i) => ({
			type: 'add',
			num: i + 1,
			oldNum: '',
			newNum: i + 1,
			text: line,
		}));
	}

	const oldLines = oldContent.split('\n');
	const newLines = newContent.split('\n');
	return lcsDiff(oldLines, newLines);
}

/**
 * LCS-based line diff. Falls back to simple diff for very large files.
 */
function lcsDiff(oldLines, newLines) {
	const n = oldLines.length, m = newLines.length;

	if (n * m > 500000) {
		return simpleDiff(oldLines, newLines);
	}

	// Use Uint32Array to support files with more than 65 535 matching lines.
	const dp = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
	for (let i = 1; i <= n; i++) {
		for (let j = 1; j <= m; j++) {
			dp[i][j] = oldLines[i - 1] === newLines[j - 1]
				? dp[i - 1][j - 1] + 1
				: Math.max(dp[i - 1][j], dp[i][j - 1]);
		}
	}

	const stack = [];
	let i = n, j = m;
	while (i > 0 || j > 0) {
		if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
			stack.push({ type: 'ctx', oldNum: i, newNum: j, text: oldLines[i - 1] });
			i--; j--;
		} else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
			stack.push({ type: 'add', oldNum: '', newNum: j, text: newLines[j - 1] });
			j--;
		} else {
			stack.push({ type: 'del', oldNum: i, newNum: '', text: oldLines[i - 1] });
			i--;
		}
	}

	stack.reverse();
	return collapseContext(stack);
}

/**
 * Simple fallback for very large files.
 * Uses Map with occurrence counts instead of Set to correctly handle
 * duplicate lines (empty lines, closing braces, etc.).
 */
function simpleDiff(oldLines, newLines) {
	/** @param {string[]} lines */
	function buildCounts(lines) {
		/** @type {Map<string, number>} */
		const map = new Map();
		for (const line of lines) {
			map.set(line, (map.get(line) || 0) + 1);
		}
		return map;
	}

	const newCounts = buildCounts(newLines);
	const oldCounts = buildCounts(oldLines);

	// Clone counts so we can decrement as we "match" lines
	const newRemaining = new Map(newCounts);
	const oldRemaining = new Map(oldCounts);

	const result = [];

	// Deletions: lines in old that have more occurrences than in new
	let oNum = 1;
	for (const line of oldLines) {
		const remaining = newRemaining.get(line) || 0;
		if (remaining > 0) {
			newRemaining.set(line, remaining - 1);
		} else {
			result.push({ type: 'del', oldNum: oNum, newNum: '', text: line });
		}
		oNum++;
	}

	// Additions: lines in new that have more occurrences than in old
	let nNum = 1;
	for (const line of newLines) {
		const remaining = oldRemaining.get(line) || 0;
		if (remaining > 0) {
			oldRemaining.set(line, remaining - 1);
		} else {
			result.push({ type: 'add', oldNum: '', newNum: nNum, text: line });
		}
		nNum++;
	}

	return result;
}

/** Show only ±3 lines of context around changes */
function collapseContext(lines, contextSize = 3) {
	const near = new Uint8Array(lines.length);
	for (let i = 0; i < lines.length; i++) {
		if (lines[i].type !== 'ctx') {
			for (let j = Math.max(0, i - contextSize); j <= Math.min(lines.length - 1, i + contextSize); j++) {
				near[j] = 1;
			}
		}
	}

	const result = [];
	let skipping = false;
	for (let i = 0; i < lines.length; i++) {
		if (near[i]) {
			skipping = false;
			result.push(lines[i]);
		} else if (!skipping) {
			skipping = true;
			result.push({ type: 'sep', oldNum: '', newNum: '', text: '···' });
		}
	}
	return result;
}

/**
 * Compute diff stats (added/removed line counts).
 */
export function diffStats(diffLines) {
	let added = 0, removed = 0;
	for (const l of diffLines) {
		if (l.type === 'add') added++;
		else if (l.type === 'del') removed++;
	}
	return { added, removed };
}
