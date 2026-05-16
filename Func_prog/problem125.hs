import qualified Data.Set as Set

main :: IO ()
main = print answer

limit :: Integer
limit = 100000000

isPalindrome :: Integer -> Bool
isPalindrome n = s == reverse s
  where
    s = show n

squares :: [Integer]
squares = takeWhile (< limit) [n * n | n <- [1..]]

palindromicSums :: [Integer]
palindromicSums = concatMap sumsFrom (tails squares)
  where
    tails [] = []
    tails xs@(_:rest) = xs : tails rest

    sumsFrom xs =
      [ total
      | (count, total) <- zip [1..] (takeWhile (< limit) (scanl1 (+) xs))
      , count >= 2
      , isPalindrome total
      ]

answer :: Integer
answer = sum (Set.toList (Set.fromList palindromicSums))
