main :: IO ()
main = putStrLn answer

reverseSuffix :: Int -> String -> String
reverseSuffix index xs = prefix ++ reverse suffix
  where
    (prefix, suffix) = splitAt index xs

nextPermutation :: String -> Maybe String
nextPermutation xs
  | null pivotIndexes = Nothing
  | otherwise = Just (take (pivot + 1) swapped ++ reverse (drop (pivot + 1) swapped))
  where
    size = length xs
    pivotIndexes = [i | i <- [0..size - 2], xs !! i < xs !! (i + 1)]
    pivot = last pivotIndexes
    swapIndex = last [i | i <- [pivot + 1..size - 1], xs !! i > xs !! pivot]

    swapped =
      [ select i
      | i <- [0..size - 1]
      ]

    select i
      | i == pivot = xs !! swapIndex
      | i == swapIndex = xs !! pivot
      | otherwise = xs !! i

rotationCount :: String -> Int
rotationCount train = arrange train 0 'A' 0
  where
    size = length train

    arrange current index expected count
      | index >= size - 1 = count
      | current !! index == expected = count
      | last current == expected && index /= size - 2 = count
      | otherwise = arrange current'' (index + 1) (succ expected) count''
      where
        targetIndex = firstIndex current expected [index + 1..size - 1]

        (current', count')
          | targetIndex < size - 1 = (reverseSuffix targetIndex current, count + 1)
          | otherwise = (current, count)

        current'' = reverseSuffix index current'
        count'' = count' + 1

    firstIndex current target (position:rest)
      | current !! position == target = position
      | otherwise = firstIndex current target rest
    firstIndex _ _ [] = size

isMaximix :: String -> Bool
isMaximix train = rotationCount train == 2 * (length train - 1) - 1

maximixArrangements :: [String]
maximixArrangements = search "CABDEFGHIJK"
  where
    search train
      | isMaximix train = train : continue
      | otherwise = continue
      where
        continue =
          case nextPermutation train of
            Just next -> search next
            Nothing -> []

answer :: String
answer = maximixArrangements !! 2010
