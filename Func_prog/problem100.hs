main :: IO ()
main = print answer

limit :: Integer
limit = 1000000000000

solutions :: [(Integer, Integer)]
solutions = iterate next (15, 21)
  where
    next (blue, total) =
      (3 * blue + 2 * total - 2, 4 * blue + 3 * total - 3)

answer :: Integer
answer = firstAboveLimit solutions
  where
    firstAboveLimit ((blue, total):rest)
      | total > limit = blue
      | otherwise = firstAboveLimit rest
    firstAboveLimit [] = 0
