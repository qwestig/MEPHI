import Control.Monad (forM_, when)
import Data.Array.ST (STUArray, newArray, readArray, runSTUArray, writeArray)
import Data.Array.Unboxed ((!))
import Control.Monad.ST (ST)

main :: IO ()
main = print answer

limit :: Integer
limit = 10000000000

primeTable :: Int -> ST s (STUArray s Int Bool)
primeTable upper = do
  table <- newArray (0, upper) True
  writeArray table 0 False
  writeArray table 1 False
  forM_ [2..floor (sqrt (fromIntegral upper :: Double))] $ \p -> do
    prime <- readArray table p
    when prime $
      forM_ [p * p, p * p + p..upper] $ \multiple ->
        writeArray table multiple False
  return table

primes :: [Integer]
primes = map fromIntegral [n | n <- [2..300000], primeFlags ! n]
  where
    primeFlags = runSTUArray (primeTable 300000)

remainder :: Integer -> Integer -> Integer
remainder n p = (2 * n * p) `mod` (p * p)

answer :: Integer
answer =
  firstMatch
    [ n
    | (n, p) <- zip [1..] primes
    , odd n
    , remainder n p > limit
    ]
  where
    firstMatch (n:_) = n
    firstMatch [] = 0
