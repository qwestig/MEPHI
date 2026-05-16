main :: IO ()
main = print answer

fibonacci :: [Integer]
fibonacci = go 1 1
  where
    go a b = a : go b (a + b)

answer :: Integer
answer = fibonacci !! 31
